import joblib
import pickle
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import numpy as np
from datetime import datetime, timezone
import re
import spacy
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Global variable for spaCy model (lazy loaded)
_nlp_model = None

def get_spacy_model():
    """Lazy load spaCy model - only loads when first needed"""
    global _nlp_model
    
    if _nlp_model is None:
        try:
            logger.info("Loading spaCy English model...")
            _nlp_model = spacy.load("en_core_web_sm")
            logger.info("✅ spaCy English model loaded successfully")
        except OSError:
            logger.warning("📥 spaCy English model not found, attempting to download...")
            try:
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                _nlp_model = spacy.load("en_core_web_sm")
                logger.info("✅ spaCy English model downloaded and loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to download spaCy model: {e}")
                logger.warning("🔧 spaCy model not available - some features may be limited")
                _nlp_model = None
    
    return _nlp_model

# Import models - maintain backward compatibility
try:
    from .models import TextExample, TrainedModel
except ImportError:
    # Define minimal classes for standalone usage
    class TextExample:
        def __init__(self, text: str, label: str):
            self.text = text
            self.label = label
    
    class TrainedModel:
        pass


class EnhancedTextPreprocessor:
    """Enhanced text preprocessing using spaCy for better feature extraction"""
    
    def __init__(self):
        self.nlp = None  # Will be loaded lazily
        self._spacy_available = False
        
        # Custom stop words for better text classification
        self.custom_stops = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
    
    def _ensure_spacy_loaded(self):
        """Ensure spaCy model is loaded when needed"""
        if self.nlp is None:
            self.nlp = get_spacy_model()
            self._spacy_available = self.nlp is not None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers (keep apostrophes for contractions)
        text = re.sub(r'[^a-zA-Z\s\']', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize_and_clean(self, text: str) -> List[str]:
        """Tokenize and clean text using spaCy if available, fallback to basic tokenization"""
        try:
            # Clean text first
            cleaned_text = self.clean_text(text)
            
            # Try to use spaCy if available
            self._ensure_spacy_loaded()
            
            if self._spacy_available and self.nlp:
                logger.debug(f"🔍 Processing text with spaCy: '{text[:50]}...'")
                
                # Process with spaCy
                doc = self.nlp(cleaned_text)
                
                # Extract tokens with advanced filtering
                filtered_tokens = []
                for token in doc:
                    # Skip stop words, punctuation, whitespace, and very short tokens
                    if (not token.is_stop and 
                        not token.is_punct and 
                        not token.is_space and 
                        len(token.text) > 2 and
                        token.text.lower() not in self.custom_stops):
                        
                        # Lemmatize the token
                        lemmatized = token.lemma_.lower()
                        filtered_tokens.append(lemmatized)
                
                logger.debug(f"✅ spaCy processing complete: {len(filtered_tokens)} filtered tokens")
                return filtered_tokens
            else:
                # Fallback to basic tokenization without spaCy
                logger.debug("⚠️ spaCy not available, using basic tokenization")
                return self._basic_tokenize(cleaned_text)
            
        except Exception as e:
            logger.error(f"❌ Error in tokenize_and_clean: {e}")
            logger.warning("⚠️ Falling back to basic tokenization")
            return self._basic_tokenize(self.clean_text(text))
    
    def _basic_tokenize(self, text: str) -> List[str]:
        """Basic tokenization fallback when spaCy is not available"""
        # Simple word splitting and filtering
        tokens = text.split()
        filtered_tokens = []
        
        for token in tokens:
            # Basic filtering
            if (len(token) > 2 and 
                token.lower() not in self.custom_stops and
                token.isalpha()):
                filtered_tokens.append(token.lower())
        
        return filtered_tokens
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for vectorization"""
        tokens = self.tokenize_and_clean(text)
        return ' '.join(tokens)


class EnhancedLogisticRegressionTrainer:
    """Enhanced training service for logistic regression text classification"""
    
    def __init__(self):
        self.preprocessor = EnhancedTextPreprocessor()
        
        # Enhanced TF-IDF vectorizer with better parameters
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,  # Increased features for better representation
            stop_words=None,  # We handle stop words in preprocessing
            ngram_range=(1, 3),  # Unigrams, bigrams, and trigrams
            min_df=2,  # Minimum document frequency (ignore very rare terms)
            max_df=0.9,  # Maximum document frequency (ignore very common terms)
            sublinear_tf=True,  # Apply sublinear tf scaling
            use_idf=True,  # Use inverse document frequency
            smooth_idf=True,  # Smooth idf weights
            norm='l2'  # L2 normalization
        )
        
        # Enhanced logistic regression with better default parameters
        self.base_model = LogisticRegression(
            max_iter=2000,  # Increased iterations
            random_state=42,
            solver='liblinear',  # Good for small datasets
            warm_start=True,  # Enable warm start for better convergence
            class_weight='balanced'  # Handle class imbalance
        )
        
        # Create pipeline for better preprocessing
        self.pipeline = Pipeline([
            ('vectorizer', self.tfidf_vectorizer),
            ('classifier', self.base_model)
        ])
        
        # Store training data for exact match checking (NEW FEATURE)
        self.training_texts = []
        self.training_labels = []
        self.is_trained = False
    
    def preprocess_data(self, examples: List[TextExample]) -> Tuple[List[str], List[str]]:
        """Extract and preprocess texts and labels from examples"""
        texts = []
        labels = []
        
        for example in examples:
            # Handle both TextExample objects and dict format
            if hasattr(example, 'text') and hasattr(example, 'label'):
                text = example.text
                label = example.label
            elif isinstance(example, dict) and 'text' in example and 'label' in example:
                text = example['text']
                label = example['label']
            else:
                continue
            
            # Preprocess text
            processed_text = self.preprocessor.preprocess_text(text)
            if processed_text.strip():  # Only include non-empty processed texts
                texts.append(processed_text)
                labels.append(label)
        
        return texts, labels
    
    def validate_dataset(self, examples: List[TextExample]) -> Tuple[bool, str]:
        """Validate dataset for training"""
        if not examples:
            return False, "No examples provided"
        
        # Check minimum examples per label
        label_counts = {}
        for example in examples:
            if hasattr(example, 'label'):
                label = example.label
            elif isinstance(example, dict) and 'label' in example:
                label = example['label']
            else:
                continue
            label_counts[label] = label_counts.get(label, 0) + 1
        
        min_examples_per_label = 2  # Minimum required for training
        max_examples_per_label = 10000
        
        for label, count in label_counts.items():
            if count < min_examples_per_label:
                return False, f"Label '{label}' has only {count} examples. Minimum required is {min_examples_per_label}"
            if count > max_examples_per_label:
                return False, f"Label '{label}' has {count} examples. Maximum allowed is {max_examples_per_label}"
        
        return True, "Dataset is valid"
    
    def find_best_hyperparameters(self, X_train: List[str], y_train: List[str]) -> Dict[str, Any]:
        """Find optimal hyperparameters using grid search"""
        print("🔍 Finding optimal hyperparameters...")
        
        # Define parameter grid for TF-IDF
        tfidf_params = {
            'vectorizer__max_features': [3000, 5000, 7000],
            'vectorizer__ngram_range': [(1, 2), (1, 3)],
            'vectorizer__min_df': [1, 2],
            'vectorizer__max_df': [0.8, 0.9, 0.95]
        }
        
        # Define parameter grid for classifier
        classifier_params = {
            'classifier__C': [0.1, 1.0, 10.0, 100.0],
            'classifier__class_weight': ['balanced', None]
        }
        
        # Combine parameter grids
        param_grid = {**tfidf_params, **classifier_params}
        
        # Use 3-fold cross-validation for hyperparameter tuning
        grid_search = GridSearchCV(
            self.pipeline,
            param_grid,
            cv=3,
            scoring='accuracy',
            n_jobs=-1,  # Use all available cores
            verbose=1
        )
        
        # Fit grid search
        grid_search.fit(X_train, y_train)
        
        print(f"✅ Best parameters: {grid_search.best_params_}")
        print(f"✅ Best cross-validation score: {grid_search.best_score_:.4f}")
        
        return {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'best_estimator': grid_search.best_estimator_
        }
    
    def train_model(self, examples: List[TextExample]) -> Dict[str, Any]:
        """Train a logistic regression model on text examples"""
        try:
            print("🚀 Starting model training...")
            print(f"📊 Training with {len(examples)} examples")
            
            # Validate dataset
            print("🔍 Validating dataset...")
            is_valid, validation_message = self.validate_dataset(examples)
            if not is_valid:
                raise ValueError(validation_message)
            print("✅ Dataset validation passed")
            
            # Preprocess data
            print("🔧 Preprocessing training data...")
            try:
                texts, labels = self.preprocess_data(examples)
                print(f"✅ Preprocessing complete: {len(texts)} processed texts, {len(labels)} labels")
            except Exception as preprocess_error:
                print(f"❌ Preprocessing failed: {preprocess_error}")
                raise Exception(f"Data preprocessing failed: {str(preprocess_error)}")
            
            # Store training data for exact match checking (NEW FEATURE)
            self.training_texts = texts[:]
            self.training_labels = labels[:]
            
            # Split data
            print("✂️ Splitting data into train/validation sets...")
            X_train, X_val, y_train, y_val = train_test_split(
                texts, labels, test_size=0.2, random_state=42, stratify=labels
            )
            print(f"✅ Data split complete: {len(X_train)} training, {len(X_val)} validation")
            
            # Find best hyperparameters
            print("🔍 Finding best hyperparameters...")
            try:
                best_params = self.find_best_hyperparameters(X_train, y_train)
                print("✅ Hyperparameter optimization complete")
            except Exception as hp_error:
                print(f"❌ Hyperparameter optimization failed: {hp_error}")
                print("⚠️ Using default parameters")
                best_params = None
            
            # Train final model
            print("🎯 Training final model...")
            if best_params and 'best_estimator' in best_params:
                best_pipeline = best_params['best_estimator']
            else:
                best_pipeline = self.pipeline
            
            # Train final model with best parameters
            print("🎯 Training final model with best parameters...")
            best_pipeline.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = best_pipeline.predict(X_val)
            accuracy = accuracy_score(y_val, y_pred)
            
            print(f"✅ Training complete! Validation accuracy: {accuracy:.4f}")
            
            # Get feature names and importance
            feature_names = best_pipeline.named_steps['vectorizer'].get_feature_names_out()
            unique_labels = list(set(labels))
            
            # Mark as trained
            self.is_trained = True
            
            # Create result dictionary (MAINTAIN OLD API FORMAT)
            result = {
                'accuracy': accuracy,
                'labels': unique_labels,
                'training_examples': len(X_train),
                'validation_examples': len(X_val),
                'total_features': len(feature_names),
                'model': best_pipeline  # This is the key field the API expects
            }
            
            print("🎉 Training completed successfully!")
            return result
            
        except Exception as e:
            print(f"❌ Training failed: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Model training failed: {str(e)}")
    
    def predict(self, text: str, model_path: str) -> Dict[str, Any]:
        """Make prediction using saved model with enhanced exact matching"""
        try:
            # Load model
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            # Handle different model formats
            if isinstance(model_data, dict):
                if 'pipeline' in model_data:
                    model = model_data['pipeline']
                    training_texts = model_data.get('training_texts', [])
                    training_labels = model_data.get('training_labels', [])
                else:
                    # Old format compatibility
                    vectorizer = model_data.get('vectorizer')
                    model = model_data.get('model')
                    if vectorizer and model:
                        # Reconstruct pipeline
                        model = Pipeline([
                            ('vectorizer', vectorizer),
                            ('classifier', model)
                        ])
                    training_texts = []
                    training_labels = []
            else:
                # Very old format - direct model object
                model = model_data
                training_texts = []
                training_labels = []
            
            # Preprocess input text
            processed_text = self.preprocessor.preprocess_text(text)
            
            # Check for exact match in training data (NEW FEATURE)
            if training_texts and training_labels:
                for i, training_text in enumerate(training_texts):
                    if processed_text == training_text:
                        exact_label = training_labels[i]
                        return {
                            'label': exact_label,
                            'confidence': 100.0,  # 100% confidence for exact matches
                            'alternatives': []
                        }
            
            # Make prediction with model
            if hasattr(model, 'predict'):
                # Pipeline format
                prediction = model.predict([processed_text])[0]
                probabilities = model.predict_proba([processed_text])[0]
                classes = model.classes_
            else:
                # Handle legacy format
                text_vector = vectorizer.transform([processed_text])
                prediction = model.predict(text_vector)[0]
                probabilities = model.predict_proba(text_vector)[0]
                classes = model.classes_
            
            # Get confidence and alternatives
            confidence = max(probabilities) * 100
            alternatives = []
            
            for i, (label, prob) in enumerate(zip(classes, probabilities)):
                if label != prediction:
                    alternatives.append({
                        'label': label,
                        'confidence': round(prob * 100, 2)
                    })
            
            # Sort alternatives by confidence
            alternatives.sort(key=lambda x: x['confidence'], reverse=True)
            
            return {
                'label': prediction,
                'confidence': round(confidence, 2),
                'alternatives': alternatives[:2]  # Top 2 alternatives
            }
            
        except Exception as e:
            logger.error(f"❌ Prediction failed: {str(e)}")
            return {
                'label': 'unknown',
                'confidence': 0.0,
                'alternatives': []
            }
    
    def predict_from_gcs(self, text: str, bucket, gcs_path: str) -> Dict[str, Any]:
        """Make prediction using model stored in GCS with enhanced exact matching"""
        try:
            # Download model from GCS
            blob = bucket.blob(gcs_path)
            model_bytes = blob.download_as_bytes()
            
            # Deserialize model data
            model_data = pickle.loads(model_bytes)
            
            # Handle different model formats
            if isinstance(model_data, dict):
                if 'pipeline' in model_data:
                    pipeline = model_data['pipeline']
                    training_texts = model_data.get('training_texts', [])
                    training_labels = model_data.get('training_labels', [])
                else:
                    # Legacy format
                    raise ValueError("Model format not supported - only complete trained pipelines are supported")
            else:
                # Very old format
                pipeline = model_data
                training_texts = []
                training_labels = []
            
            # Preprocess input text
            processed_text = self.preprocessor.preprocess_text(text)
            
            # Check for exact match in training data (NEW FEATURE)
            if training_texts and training_labels:
                for i, training_text in enumerate(training_texts):
                    if processed_text == training_text:
                        exact_label = training_labels[i]
                        return {
                            'label': exact_label,
                            'confidence': 100.0,  # 100% confidence for exact matches
                            'alternatives': []
                        }
            
            # Make prediction using the pipeline
            prediction = pipeline.predict([processed_text])[0]
            probabilities = pipeline.predict_proba([processed_text])[0]
            
            # Get confidence and alternatives
            confidence = max(probabilities) * 100
            alternatives = []
            
            # Get class labels from the pipeline
            classes = pipeline.classes_
            
            for i, (label, prob) in enumerate(zip(classes, probabilities)):
                if label != prediction:
                    alternatives.append({
                        'label': label,
                        'confidence': round(prob * 100, 2)
                    })
            
            # Sort alternatives by confidence
            alternatives.sort(key=lambda x: x['confidence'], reverse=True)
            
            return {
                'label': prediction,
                'confidence': round(confidence, 2),
                'alternatives': alternatives[:2]  # Top 2 alternatives
            }
            
        except Exception as e:
            raise Exception(f"Failed to load model from GCS: {str(e)}")
    
    def save_model(self, model_path: str) -> str:
        """Save trained model and vectorizer with training data"""
        if not self.is_trained:
            raise ValueError("No trained model to save")
        
        # Get the trained pipeline from the last training
        # This assumes the model was stored after training
        model_data = {
            'pipeline': self.pipeline,  # Save the complete pipeline
            'training_texts': self.training_texts,  # NEW: For exact matching
            'training_labels': self.training_labels,  # NEW: For exact matching
            'trained_at': datetime.now(timezone.utc).isoformat()
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        return model_path
    
    def save_model_to_gcs(self, bucket, gcs_path: str, trained_pipeline) -> str:
        """Save trained model directly to GCS with training data"""
        if trained_pipeline is None:
            raise ValueError("Trained pipeline is required - cannot save untrained models")
        
        # Save the complete trained pipeline with training data
        model_data = {
            'pipeline': trained_pipeline,  # Save the complete trained pipeline
            'training_texts': self.training_texts,  # NEW: For exact matching
            'training_labels': self.training_labels,  # NEW: For exact matching
            'trained_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Serialize model data
        model_bytes = pickle.dumps(model_data)
        
        # Upload to GCS
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(model_bytes, content_type='application/octet-stream')
        
        return gcs_path


# Global trainer instance - MAINTAIN OLD API COMPATIBILITY
trainer = EnhancedLogisticRegressionTrainer()