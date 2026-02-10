import { PlusIcon } from '@heroicons/react/24/outline';

/**
 * Reusable empty state component
 */
export default function EmptyState({ 
  icon: Icon, 
  title, 
  message, 
  actionLabel, 
  onAction,
  iconClassName = "w-16 h-16 text-gray-600"
}) {
  return (
    <div className="text-center py-12">
      {Icon && <Icon className={`${iconClassName} mx-auto mb-4`} />}
      <p className="text-gray-400 mb-4 text-lg">{title}</p>
      {message && <p className="text-gray-500 mb-4">{message}</p>}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-6 py-2 bg-white text-black rounded-full font-medium hover:scale-105 transition-transform"
        >
          {Icon && Icon === PlusIcon && <PlusIcon className="w-5 h-5 inline mr-2" />}
          {actionLabel}
        </button>
      )}
    </div>
  );
}
