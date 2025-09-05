import Navigation from './Navigation';

interface MobileMenuProps {
  isOpen: boolean;
  links?: string[];
  className?: string;
}

export default function MobileMenu({ 
  isOpen, 
  links,
  className = ''
}: MobileMenuProps) {
  if (!isOpen) return null;

  return (
    <div className={`md:hidden ${className}`}>
      <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-[#1c1c1c] border-t border-[#bc6cd3]/20">
        <Navigation links={links} isMobile={true} />
        
        {/* Mobile Yaaralabs.ai branding */}
        <div className="flex items-center justify-center space-x-2 px-3 py-2 border-t border-[#bc6cd3]/20 mt-4 pt-4">
          <img 
            src="/yaaralogo.jpg" 
            alt="Yaaralabs.ai Logo" 
            className="h-6 w-6 rounded-full"
          />
          <span className="font-bold text-white text-sm">
            Yaaralabs.ai
          </span>
        </div>
      </div>
    </div>
  );
}
