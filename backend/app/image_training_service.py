import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
from tensorflow.keras.preprocessing import image
import os
import tempfile
import time
import shutil
import zipfile
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import logging
from google.cloud import storage
from google.cloud import firestore
import json
import gc
import time
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logger = logging.getLogger(__name__)

class ImageRecognitionTrainer:
    """Ultra-lightweight training service optimized for small datasets (5-10 images per class)"""
    
    def __init__(self):
        self.img_size = (128, 128)  # Smaller images for faster processing
        self.batch_size = 8  # Larger batch size for efficiency
        self.epochs = 20  # Much fewer epochs for speed
        self.model = None
        self.class_names = []
        self.is_trained = False
        self.use_lightweight = True  # Use lightweight MobileNetV2

        
    def prepare_training_data_direct(self, image_examples: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare training data directly from GCS images with minimal augmentation for speed"""
        try:
            # Group images by label
            label_groups = {}
            for example in image_examples:
                label = example.get('label', 'unknown')
                image_url = example.get('image_url', '')
                
                if not image_url or not label:
                    continue
                    
                if label not in label_groups:
                    label_groups[label] = []
                label_groups[label].append(image_url)
            
            # Process images directly from GCS with minimal augmentation
            images = []
            labels = []
            class_names = []
            label_to_idx = {}
            
            for label, image_urls in label_groups.items():
                if len(image_urls) < 1:  # Allow single image per class
                    continue
                    
                if label not in label_to_idx:
                    label_to_idx[label] = len(class_names)
                    class_names.append(label)
                
                label_idx = label_to_idx[label]
                
                # Process each image with minimal augmentation for speed
                for i, image_url in enumerate(image_urls):
                    try:
                        # Download image directly to memory
                        image_data = self._download_image_to_memory(image_url)
                        if image_data is not None:
                            # Add original image
                            images.append(image_data)
                            labels.append(label_idx)
                            
                            # Apply minimal augmentation (only 3x for speed)
                            augmented_images = self._apply_minimal_augmentation(image_data)
                            for aug_img in augmented_images:
                                images.append(aug_img)
                                labels.append(label_idx)
                            
                            logger.info(f"Processed image {i+1}/{len(image_urls)} for label '{label}' with {len(augmented_images)} augmentations")
                        
                    except Exception as e:
                        logger.warning(f"Failed to process image {image_url}: {e}")
                        continue
            
            if not class_names:
                raise ValueError("No valid image data found for training")
            
            # Convert to numpy arrays
            images_array = np.array(images)
            labels_array = np.array(labels)
            
            logger.info(f"Prepared training data: {len(class_names)} classes, {len(images)} total images")
            logger.info(f"Images shape: {images_array.shape}, Labels shape: {labels_array.shape}")
            
            return images_array, labels_array, class_names
            
        except Exception as e:
            logger.error(f"Error preparing training data directly: {e}")
            raise Exception(f"Failed to prepare training data: {str(e)}")
    
    def _apply_minimal_augmentation(self, image: np.ndarray) -> List[np.ndarray]:
        """Apply minimal data augmentation for speed"""
        augmented_images = []
        
        try:
            # Create ImageDataGenerator with minimal augmentation for speed
            datagen = ImageDataGenerator(
                rotation_range=15,  # Small rotation
                width_shift_range=0.1,  # Small shift
                height_shift_range=0.1,  # Small shift
                horizontal_flip=True,  # Only horizontal flip
                brightness_range=[0.9, 1.1],  # Small brightness change
                fill_mode='nearest'
            )
            
            # Reshape image for augmentation (add batch dimension)
            image_batch = np.expand_dims(image, axis=0)
            
            # Generate only 3 augmented versions for speed
            aug_iter = datagen.flow(image_batch, batch_size=1, shuffle=False)
            
            for _ in range(3):  # Only 3 augmented versions for speed
                aug_image = next(aug_iter)[0]  # Get first (and only) image from batch
                augmented_images.append(aug_image)
                
        except Exception as e:
            logger.warning(f"Augmentation failed: {e}")
            # If augmentation fails, return empty list (original image already added)
            
        return augmented_images
    
    def _download_image_to_memory(self, gcs_url: str) -> Optional[np.ndarray]:
        """Download image from GCS URL directly to memory and return as numpy array"""
        try:
            # Initialize GCS client
            client = storage.Client()
            
            # Parse GCS URL to get bucket and blob name
            if gcs_url.startswith('gs://'):
                url_parts = gcs_url[5:].split('/', 1)
                bucket_name = url_parts[0]
                blob_name = url_parts[1]
            else:
                raise ValueError(f"Invalid GCS URL format: {gcs_url}")
            
            # Download the blob to memory
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            image_bytes = blob.download_as_bytes()
            
            # Convert bytes to PIL Image
            from PIL import Image
            import io
            
            logger.info(f"Downloaded {len(image_bytes)} bytes from GCS: {gcs_url}")
            
            # Debug: Check the first few bytes to see what format it might be
            header = image_bytes[:20]
            logger.info(f"Image header bytes: {header}")
            logger.info(f"Image header as hex: {header.hex()}")
            
            # Check if it's a valid image format
            if image_bytes.startswith(b'\xff\xd8\xff'):
                logger.info("Detected JPEG format")
            elif image_bytes.startswith(b'\x89PNG'):
                logger.info("Detected PNG format")
            elif image_bytes.startswith(b'GIF8'):
                logger.info("Detected GIF format")
            elif image_bytes.startswith(b'RIFF') and b'WEBP' in image_bytes[:12]:
                logger.info("Detected WebP format")
            else:
                logger.warning(f"Unknown image format. Header: {header}")
            
            try:
                pil_image = Image.open(io.BytesIO(image_bytes))
                logger.info(f"Successfully opened image: {pil_image.format}, {pil_image.mode}, {pil_image.size}")
            except Exception as img_error:
                logger.error(f"Failed to open image from bytes: {img_error}")
                # Try to save the bytes to a file for debugging
                debug_path = f"debug_image_{int(time.time())}.bin"
                with open(debug_path, 'wb') as f:
                    f.write(image_bytes)
                logger.error(f"Saved problematic image bytes to: {debug_path}")
                raise ValueError(f"Cannot identify image file: {img_error}")
            
            # Convert to RGB if needed
            if pil_image.mode != 'RGB':
                logger.info(f"Converting image from {pil_image.mode} to RGB")
                pil_image = pil_image.convert('RGB')
            
            # Resize to target size
            pil_image = pil_image.resize(self.img_size)
            logger.info(f"Resized image to: {pil_image.size}")
            
            # Convert to numpy array
            img_array = np.array(pil_image)
            logger.info(f"Converted to numpy array: {img_array.shape}, dtype: {img_array.dtype}")
            
            # Normalize to [0, 1] range
            img_array = img_array.astype(np.float32) / 255.0
            
            return img_array
            
        except Exception as e:
            logger.error(f"Failed to download image from GCS to memory: {e}")
            raise e
    
    def _download_image_from_gcs(self, gcs_url: str, local_path: str):
        """Download image from GCS URL to local path - FIXED VERSION"""
        try:
            # Initialize GCS client
            client = storage.Client()
            
            # Parse GCS URL to get bucket and blob name
            if gcs_url.startswith('gs://'):
                url_parts = gcs_url[5:].split('/', 1)
                bucket_name = url_parts[0]
                blob_name = url_parts[1]
            else:
                raise ValueError(f"Invalid GCS URL format: {gcs_url}")
            
            # Download the blob to memory
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            image_bytes = blob.download_as_bytes()
            
            # Save image to local path
            with open(local_path, 'wb') as f:
                f.write(image_bytes)
            
            # FIXED: Keep images in RGB format for EfficientNet
            try:
                from PIL import Image
                img = Image.open(local_path)
                if img.mode != 'RGB':  # Convert to RGB, not grayscale
                    logger.info(f"Converting image from {img.mode} to RGB: {local_path}")
                    img = img.convert('RGB')  # Convert to RGB (3 channels)
                    img.save(local_path, 'JPEG')
                    logger.info(f"Image converted to RGB and saved: {local_path}")
            except Exception as convert_error:
                logger.warning(f"Could not convert image to RGB: {convert_error}")
            
        except Exception as e:
            logger.error(f"Failed to download image from GCS: {e}")
            raise
    
    def train_model_direct(self, images: np.ndarray, labels: np.ndarray, class_names: List[str]) -> Dict[str, Any]:
        """Train ultra-lightweight MobileNetV2 model optimized for small datasets"""
        try:
            logger.info("🚀 Starting ultra-lightweight MobileNetV2 training for small datasets...")
            logger.info(f"📊 Training with {len(class_names)} classes: {class_names}")
            logger.info(f"📊 Training with {len(images)} images, shape: {images.shape}")
            
            # Clear everything
            logger.info("🧹 Performing cleanup...")
            self.model = None
            self.is_trained = False
            
            # Clear TensorFlow completely
            self.nuclear_tensorflow_reset()
            
            # Get number of classes
            num_classes = len(class_names)
            self.class_names = class_names
            
            logger.info(f"📊 Detected {num_classes} classes: {class_names}")
            
            # Verify input data is RGB
            if len(images.shape) != 4:
                raise ValueError(f"Expected 4D image array, got shape: {images.shape}")
            
            actual_channels = images.shape[3]
            logger.info(f"✅ Confirmed image data has {actual_channels} channels (RGB)")
            
            if actual_channels != 3:
                raise ValueError(f"MobileNetV2 requires RGB images (3 channels), got {actual_channels} channels")
            
            # Build ultra-lightweight MobileNetV2 model
            logger.info("🔄 Creating ultra-lightweight MobileNetV2 model...")
            
            try:
                # Create MobileNetV2 base model (much smaller than ResNet50)
                base_model = MobileNetV2(
                    include_top=False,
                    weights="imagenet",
                    input_shape=(128, 128, 3),  # Smaller input size
                    alpha=0.35  # Smaller alpha for even lighter model
                )
                logger.info("✅ MobileNetV2 base model created successfully")
                
            except Exception as e:
                logger.error(f"MobileNetV2 creation failed: {e}")
                raise Exception(f"Failed to create MobileNetV2 model: {e}")
            
            # Freeze base model initially
            base_model.trainable = False
            
            # Build simple classifier for speed
            inputs = keras.Input(shape=(128, 128, 3), name='rgb_input')
            x = base_model(inputs, training=False)
            x = layers.GlobalAveragePooling2D()(x)
            x = layers.Dropout(0.2)(x)  # Minimal dropout for speed
            outputs = layers.Dense(num_classes, activation="softmax", name='predictions')(x)
            
            self.model = keras.Model(inputs, outputs, name=f'mobilenetv2_lightweight_{num_classes}classes')
            
            # Compile with higher learning rate for faster convergence
            self.model.compile(
                optimizer=keras.optimizers.Adam(learning_rate=0.01),  # Higher LR for speed
                loss="sparse_categorical_crossentropy",
                metrics=["accuracy"]
            )
            
            logger.info(f"🏗️ Model built with {num_classes} output classes")
            logger.info(f"📋 Final model input shape: {self.model.input_shape}")
            logger.info(f"📋 Final model output shape: {self.model.output_shape}")
            
            # Print model summary
            self.model.summary(print_fn=logger.info)
            
            # Verify model accepts our data shape
            logger.info(f"🔍 Verifying model accepts data shape: {images.shape}")
            try:
                test_pred = self.model.predict(images[:1], verbose=0)
                logger.info(f"✅ Model verification successful, output shape: {test_pred.shape}")
            except Exception as verify_error:
                logger.error(f"❌ Model verification failed: {verify_error}")
                raise Exception(f"Model cannot process input data: {verify_error}")
            
            # Single phase training for speed
            logger.info("🎯 Training with frozen base model (single phase for speed)...")
            history = self.model.fit(
                images, 
                labels, 
                epochs=self.epochs,  # Only 20 epochs for speed
                batch_size=self.batch_size, 
                verbose=1,
                validation_split=0.2 if len(images) > 4 else 0,
                callbacks=[
                    keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),  # More patience for small datasets
                    keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5, min_lr=1e-4)  # More stable LR reduction
                ]
            )
            
            # Get final accuracy
            final_accuracy = history.history['accuracy'][-1] if 'accuracy' in history.history else 0.0
            final_loss = history.history['loss'][-1] if 'loss' in history.history else 0.0
            
            logger.info(f"✅ Training complete! Final accuracy: {final_accuracy:.4f}")
            
            # Mark as trained
            self.is_trained = True
            
            # Create result dictionary
            result = {
                'accuracy': final_accuracy,
                'loss': final_loss,
                'labels': class_names,
                'num_classes': num_classes,
                'training_examples': len(images),
                'model': self.model,
                'class_names': class_names,
                'img_size': self.img_size
            }
            
            logger.info("🎉 Ultra-lightweight MobileNetV2 training completed successfully!")
            return result
            
        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            logger.error(f"❌ Error details: {str(e)}")
            raise Exception(f"Image model training failed: {str(e)}")
    
    def nuclear_tensorflow_reset(self):
        """Nuclear option: Complete TensorFlow reset"""
        try:
            logger.info("🚀 NUCLEAR TENSORFLOW RESET - clearing everything...")
            
            # Clear backend
            tf.keras.backend.clear_session()
            
            # Force garbage collection
            gc.collect()
            
            # Clear default graph
            try:
                tf.compat.v1.reset_default_graph()
            except:
                pass
                
            # Delete all cached directories aggressively
            import platform
            home = os.path.expanduser("~")
            
            cache_patterns = [
                os.path.join(home, ".keras", "models"),
                os.path.join(home, ".keras", "datasets"),
                os.path.join(home, ".cache", "tensorflow"),
                os.path.join(home, ".cache", "keras"),
                os.path.join(home, ".tensorflow"),
            ]
            
            # Windows specific paths
            if platform.system() == "Windows":
                cache_patterns.extend([
                    os.path.join(os.environ.get('APPDATA', ''), 'keras'),
                    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'tensorflow'),
                ])
            
            for cache_path in cache_patterns:
                if os.path.exists(cache_path):
                    try:
                        shutil.rmtree(cache_path)
                        logger.info(f"💥 Nuked cache: {cache_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not nuke {cache_path}: {e}")
            
            # Clear environment variables that might affect caching
            env_vars_to_clear = [
                'TF_CPP_MIN_LOG_LEVEL',
                'KERAS_BACKEND',
                'TF_FORCE_GPU_ALLOW_GROWTH'
            ]
            
            for env_var in env_vars_to_clear:
                if env_var in os.environ:
                    del os.environ[env_var]
            
            # Pause to ensure cleanup
            time.sleep(2)
            
            # Force another garbage collection
            gc.collect()
            
            logger.info("✅ Nuclear reset completed!")
            
        except Exception as e:
            logger.warning(f"⚠️ Nuclear reset encountered issues: {e}")
    
    def predict_image(self, img_path: str) -> Dict[str, Any]:
        """Make prediction on a single image using ultra-lightweight MobileNetV2"""
        try:
            if not self.is_trained or not self.model:
                raise ValueError("Model not trained yet")
            
            # Load and preprocess image
            img = image.load_img(img_path, target_size=self.img_size, color_mode='rgb')
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x = x.astype(np.float32) / 255.0
            
            # Make prediction with the trained model
            preds = self.model.predict(x, verbose=0)
            predicted_class_idx = np.argmax(preds)
            confidence = float(np.max(preds) * 100)  # Convert to percentage and ensure float
            
            # Get predicted class name
            predicted_class = self.class_names[predicted_class_idx]
            
            # Get all class probabilities
            all_probabilities = []
            for i, class_name in enumerate(self.class_names):
                prob_percentage = preds[0][i] * 100
                all_probabilities.append({
                    'class': class_name,
                    'confidence': float(round(prob_percentage, 2))
                })
            
            # Sort by confidence
            all_probabilities.sort(key=lambda x: x['confidence'], reverse=True)
            
            logger.info(f"🔮 MobileNetV2 Prediction: {predicted_class} ({confidence:.2f}% confidence)")
            prob_strings = [f"{p['class']}: {p['confidence']:.1f}%" for p in all_probabilities]
            logger.info(f"📊 All probabilities: {prob_strings}")
            
            return {
                'predicted_class': predicted_class,
                'confidence': float(round(confidence, 2)),
                'all_probabilities': all_probabilities
            }
            
        except Exception as e:
            logger.error(f"❌ Prediction failed: {e}")
            return {
                'predicted_class': 'unknown',
                'confidence': float(0.0),
                'all_probabilities': []
            }
    
    def predict_from_gcs(self, gcs_url: str) -> Dict[str, Any]:
        """Make prediction using image from GCS URL"""
        try:
            # Download image directly to memory
            img_array = self._download_image_to_memory(gcs_url)
            
            # Make prediction using the image array
            if self.model is None:
                raise ValueError("Model not loaded")
            
            # Reshape for model input (add batch dimension)
            img_array = np.expand_dims(img_array, axis=0)
            
            # Make prediction
            predictions = self.model.predict(img_array, verbose=0)
            
            # Get the predicted class
            predicted_class_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class_idx]) * 100  # Convert to percentage
            predicted_class = self.class_names[predicted_class_idx]
            
            # Get all probabilities
            all_probabilities = []
            for i, prob in enumerate(predictions[0]):
                all_probabilities.append({
                    'class': self.class_names[i],
                    'confidence': float(prob) * 100  # Convert to percentage
                })
            
            # Sort by confidence
            all_probabilities.sort(key=lambda x: x['confidence'], reverse=True)
            
            return {
                'predicted_class': predicted_class,
                'confidence': confidence,
                'all_probabilities': all_probabilities
            }
                    
        except Exception as e:
            logger.error(f"❌ GCS prediction failed: {e}")
            return {
                'predicted_class': 'unknown',
                'confidence': float(0.0),
                'all_probabilities': []
            }
    
    def save_model(self, bucket, gcs_path: str) -> str:
        """Save ultra-lightweight MobileNetV2 model to GCS"""
        try:
            if not self.is_trained or not self.model:
                raise ValueError("No trained model to save")
            
            # Create lightweight metadata
            metadata = {
                'class_names': self.class_names,
                'img_size': self.img_size,
                'num_classes': len(self.class_names),
                'color_mode': 'rgb',
                'model_type': 'mobilenetv2_lightweight',
                'trained_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Save metadata directly to GCS
            metadata_gcs_path = f"{gcs_path}/metadata.json"
            metadata_blob = bucket.blob(metadata_gcs_path)
            metadata_blob.upload_from_string(json.dumps(metadata, indent=2))
            logger.info(f"Uploaded metadata to {metadata_gcs_path}")
            
            # Save main model
            model_gcs_path = f"{gcs_path}/saved_model"
            
            with tempfile.NamedTemporaryFile(suffix='.keras', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Save main model
                self.model.save(temp_path)
                
                with open(temp_path, 'rb') as f:
                    model_data = f.read()
                
                model_blob = bucket.blob(f"{model_gcs_path}.keras")
                model_blob.upload_from_string(model_data)
                logger.info(f"Uploaded lightweight model to {model_gcs_path}.keras")
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
            logger.info(f"✅ Ultra-lightweight MobileNetV2 model saved to GCS: {gcs_path}")
            return gcs_path
            
        except Exception as e:
            logger.error(f"❌ Failed to save model: {e}")
            raise Exception(f"Failed to save model: {str(e)}")
    
    def load_model_from_gcs(self, bucket, gcs_path: str) -> bool:
        """Load ultra-lightweight MobileNetV2 model from GCS"""
        try:
            logger.info(f"Loading ultra-lightweight MobileNetV2 model from GCS path: {gcs_path}")
            
            # Load metadata first
            metadata_gcs_path = f"{gcs_path}/metadata.json"
            logger.info(f"Loading metadata from: {metadata_gcs_path}")
            metadata_blob = bucket.blob(metadata_gcs_path)
            metadata_data = metadata_blob.download_as_text()
            metadata = json.loads(metadata_data)
            logger.info(f"Metadata loaded: {metadata}")
            
            # Load main model
            model_gcs_path = f"{gcs_path}/saved_model.keras"
            logger.info(f"Loading lightweight model from: {model_gcs_path}")
            model_blob = bucket.blob(model_gcs_path)
            
            with tempfile.NamedTemporaryFile(suffix='.keras', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Download and load main model
                model_blob.download_to_filename(temp_path)
                self.model = keras.models.load_model(temp_path, compile=False)
                
                # Recompile the model
                self.model.compile(
                    optimizer=keras.optimizers.Adam(0.01),
                    loss="sparse_categorical_crossentropy",
                    metrics=["accuracy"]
                )
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
            # Restore model state
            self.class_names = metadata['class_names']
            self.img_size = metadata['img_size']
            self.is_trained = True
            
            # Log model info
            model_type = metadata.get('model_type', 'unknown')
            color_mode = metadata.get('color_mode', 'unknown')
            logger.info(f"Model loaded - Type: {model_type}, Color mode: {color_mode}")
            
            logger.info(f"✅ Ultra-lightweight MobileNetV2 model loaded from GCS: {gcs_path}")
            return True
                
        except Exception as e:
            logger.error(f"❌ Failed to load model from GCS: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            logger.error(f"❌ Error details: {str(e)}")
            return False
    
    def update_firestore_training_status(self, project_id: str, session_id: str, status: str, 
                                       training_result: Optional[Dict[str, Any]] = None, 
                                       model_gcs_path: Optional[str] = None) -> bool:
        """Update Firestore with training status for a specific project and session"""
        try:
            # Initialize Firestore client
            db = firestore.Client()
            
            # Find the project document where createdBy contains the session_id
            projects_collection = db.collection('projects')
            query = projects_collection.where(filter=firestore.FieldFilter("createdBy", "==", f"guest:{session_id}")).where(filter=firestore.FieldFilter("id", "==", project_id)).limit(1)
            docs = list(query.stream())
            
            if not docs:
                logger.error(f"No project found with ID {project_id} for session {session_id}")
                return False
            
            doc_ref = docs[0].reference
            
            # Prepare update data
            update_data = {
                'updatedAt': datetime.now(timezone.utc)
            }
            
            if status == "training":
                update_data['status'] = "training"
                update_data['trainingStartedAt'] = datetime.now(timezone.utc)
            elif status == "completed":
                update_data['status'] = "trained"
                update_data['trainingCompletedAt'] = datetime.now(timezone.utc)
                
                if training_result:
                    update_data['model.accuracy'] = training_result.get('accuracy', 0.0)
                    update_data['model.loss'] = training_result.get('loss', 0.0)
                    update_data['model.labels'] = training_result.get('class_names', [])
                    update_data['model.numClasses'] = training_result.get('num_classes', 0)
                    update_data['model.trainedAt'] = datetime.now(timezone.utc)
                    
                if model_gcs_path:
                    update_data['model.gcsPath'] = model_gcs_path
                    update_data['model.filename'] = f"image_model_{project_id}"
                    update_data['model.modelType'] = "efficientnet"
                    update_data['model.endpointUrl'] = f"/api/guests/session/{session_id}/projects/{project_id}/predict"
                    
            elif status == "failed":
                update_data['status'] = "failed"
                update_data['trainingFailedAt'] = datetime.now(timezone.utc)
            
            # Update the document
            doc_ref.update(update_data)
            
            logger.info(f"✅ Updated Firestore for project {project_id} with status: {status}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update Firestore: {e}")
            return False

    def clear_existing_model(self, bucket, gcs_path: str) -> bool:
        """Clear existing model from GCS to prevent shape mismatch issues"""
        try:
            # List all files in the GCS directory
            blobs = bucket.list_blobs(prefix=gcs_path)
            deleted_count = 0
            
            for blob in blobs:
                blob.delete()
                deleted_count += 1
                logger.info(f"Deleted {blob.name}")
            
            logger.info(f"✅ Cleared {deleted_count} files from {gcs_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear existing model: {e}")
            return False

    def clear_tensorflow_cache(self):
        """Clear TensorFlow model cache to avoid cached weight issues - DEPRECATED, use nuclear_tensorflow_reset"""
        logger.info("⚠️ Using legacy cache clear - consider using nuclear_tensorflow_reset()")
        self.nuclear_tensorflow_reset()

    def cleanup_temp_files(self, train_dir: str):
        """Clean up temporary training directory"""
        try:
            if os.path.exists(train_dir):
                shutil.rmtree(train_dir)
                logger.info(f"✅ Cleaned up temporary directory: {train_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to clean up temporary directory: {e}")


# Global trainer instance
image_trainer = ImageRecognitionTrainer()