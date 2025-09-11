'use client';

import { useState, useEffect } from 'react';
import config from '../../lib/config';

interface ImageExample {
  image_url: string;
  label: string;
  filename: string;
}

interface ImageGalleryProps {
  images: ImageExample[];
  onDelete?: (imageUrl: string) => void;
  isLoading?: boolean;
  sessionId?: string;
  projectId?: string;
}

export default function ImageGallery({ images, onDelete, isLoading, sessionId, projectId }: ImageGalleryProps) {
  const [selectedImage, setSelectedImage] = useState<ImageExample | null>(null);
  const [groupedImages, setGroupedImages] = useState<Record<string, ImageExample[]>>({});

  // Debug logging
  useEffect(() => {
    console.log('🖼️ ImageGallery received images:', images);
    if (images.length > 0) {
      console.log('🖼️ First image object:', images[0]);
      console.log('🖼️ Image URL:', images[0]?.image_url);
    }
  }, [images]);

  // Group images by label
  useEffect(() => {
    console.log('🖼️ Grouping images:', images);
    const grouped = images.reduce((acc, image) => {
      if (!acc[image.label]) {
        acc[image.label] = [];
      }
      acc[image.label].push(image);
      return acc;
    }, {} as Record<string, ImageExample[]>);
    console.log('🖼️ Grouped images:', grouped);
    setGroupedImages(grouped);
  }, [images]);

  const getImageUrl = (gcsUrl: string) => {
    console.log('🖼️ Converting GCS URL:', gcsUrl);
    // Convert GCS URL to use our backend endpoint
    if (gcsUrl.startsWith('gs://') && sessionId && projectId) {
      // Extract the path after the bucket name
      // gs://playgroundai-470111-data/images/project_id/label/filename
      const parts = gcsUrl.split('/');
      const imagesIndex = parts.findIndex(part => part === 'images');
      if (imagesIndex !== -1 && imagesIndex < parts.length - 1) {
        // Get everything after 'images/project_id/' (skip the project_id part)
        const pathAfterImages = parts.slice(imagesIndex + 1);
        if (pathAfterImages.length > 1) {
          // Skip the first part (project_id) and join the rest (label/filename)
          const imagePath = pathAfterImages.slice(1).join('/');
          const backendUrl = `${config.apiBaseUrl}/api/guests/session/${sessionId}/projects/${projectId}/images/${imagePath}`;
          console.log('🖼️ Converted to backend URL:', backendUrl);
          return backendUrl;
        }
      }
    }
    console.log('🖼️ Using URL as-is:', gcsUrl);
    return gcsUrl;
  };

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#dcfc84] mx-auto"></div>
        <p className="text-white/70 mt-2">Loading images...</p>
      </div>
    );
  }

  if (images.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl text-white/20 mb-4">📷</div>
        <p className="text-white/70 text-lg">No images uploaded yet</p>
        <p className="text-white/50 text-sm mt-2">Upload some images to get started</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Summary */}
      <div className="bg-[#2a2a2a] rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-white">Image Collection</h3>
            <p className="text-white/70 text-sm">
              {images.length} image{images.length !== 1 ? 's' : ''} across {Object.keys(groupedImages).length} label{Object.keys(groupedImages).length !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-white/50">Labels:</p>
            <div className="flex flex-wrap gap-2 mt-1">
              {Object.keys(groupedImages).map(label => (
                <span
                  key={label}
                  className="bg-[#dcfc84] text-[#1c1c1c] px-2 py-1 rounded text-xs font-medium"
                >
                  {label} ({groupedImages[label].length})
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Images by Label */}
      {Object.entries(groupedImages).map(([label, labelImages]) => (
        <div key={label} className="space-y-4">
          <h4 className="text-lg font-medium text-white flex items-center">
            <span className="bg-[#dcfc84] text-[#1c1c1c] px-3 py-1 rounded-full text-sm font-medium mr-3">
              {label}
            </span>
            <span className="text-white/70 text-sm">
              {labelImages.length} image{labelImages.length !== 1 ? 's' : ''}
            </span>
          </h4>
          
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {labelImages.map((image, index) => (
              <div
                key={`${image.label}-${index}`}
                className="relative group cursor-pointer"
                onClick={() => setSelectedImage(image)}
              >
                <div className="aspect-square rounded-lg overflow-hidden border border-[#bc6cd3]/20 hover:border-[#dcfc84] transition-colors">
                  <img
                    src={getImageUrl(image.image_url)}
                    alt={`${image.label} example`}
                    className="w-full h-full object-cover"
                    onLoad={() => console.log('🖼️ Image loaded successfully:', image.filename)}
                    onError={(e) => {
                      console.log('🖼️ Image failed to load:', image.filename, 'URL:', getImageUrl(image.image_url));
                      // Fallback for images that can't be loaded
                      const target = e.target as HTMLImageElement;
                      target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iIzMzMzMzMyIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNjY2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2U8L3RleHQ+PC9zdmc+';
                    }}
                  />
                </div>
                
                {/* Hover overlay */}
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-white text-xs font-medium mb-1">View</p>
                    {onDelete && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete(image.image_url);
                        }}
                        className="text-red-400 hover:text-red-300 text-xs"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
                
                <p className="text-xs text-white/70 mt-1 truncate">
                  {image.filename}
                </p>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Image Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div className="max-w-4xl max-h-full bg-[#1c1c1c] rounded-lg overflow-hidden">
            <div className="p-4 border-b border-[#bc6cd3]/20 flex items-center justify-between">
              <h3 className="text-lg font-medium text-white">
                {selectedImage.label} - {selectedImage.filename}
              </h3>
              <button
                onClick={() => setSelectedImage(null)}
                className="text-white/70 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            <div className="p-4">
              <img
                src={getImageUrl(selectedImage.image_url)}
                alt={`${selectedImage.label} example`}
                className="max-w-full max-h-[70vh] object-contain mx-auto"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iIzMzMzMzMyIvPjx0ZXh0IHg9IjIwMCIgeT0iMTUwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjQiIGZpbGw9IiM2NjYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZSBVbmF2YWlsYWJsZTwvdGV4dD48L3N2Zz4=';
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
