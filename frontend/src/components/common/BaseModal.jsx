import { XMarkIcon } from '@heroicons/react/24/outline';

/**
 * Base modal component for consistent modal styling
 */
export default function BaseModal({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  maxWidth = 'max-w-md',
  showCloseButton = true 
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
      <div className={`bg-gray-900 rounded-lg w-full ${maxWidth} relative`}>
        {showCloseButton && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
            aria-label="Close modal"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        )}
        {title && (
          <div className="p-6 pb-4 border-b border-gray-800">
            <h2 className="text-2xl font-bold text-white">{title}</h2>
          </div>
        )}
        <div className={title ? 'p-6' : 'p-6'}>
          {children}
        </div>
      </div>
    </div>
  );
}
