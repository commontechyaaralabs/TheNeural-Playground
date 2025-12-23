'use client';

import { useState } from 'react';
import Logo from './Logo';
import Navigation from './Navigation';
import MobileMenuButton from './MobileMenuButton';
import MobileMenu from './MobileMenu';

interface HeaderProps {
  className?: string;
  logoSize?: 'sm' | 'md' | 'lg';
  navigationLinks?: string[];
  showMobileMenu?: boolean;
  fixed?: boolean;
  transparent?: boolean;
  theme?: 'dark' | 'light';
  showAboutLink?: boolean;
}

export default function Header({
  className = '',
  logoSize = 'md',
  showMobileMenu = true,
  fixed = true,
  transparent = false,
  theme = 'dark',
  showAboutLink = false
}: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const headerClasses = `
    ${fixed ? 'fixed top-0' : 'relative'} 
    w-full z-50 
    ${transparent ? 'bg-transparent' : className.includes('bg-white') ? className : 'bg-[#1c1c1c]'} 
    ${className.includes('border-gray-200') ? className.includes('border-b') ? '' : 'border-b border-gray-200' : 'border-b border-[#bc6cd3]/20'} 
    backdrop-blur-sm
    ${className}
  `.trim();

  return (
    <header className={headerClasses}>
      <nav className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Logo */}
          <div className="flex-shrink-0">
            <Logo size={logoSize} theme={theme} />
          </div>
          
          {/* Center: Desktop Navigation */}
          <div className="hidden md:block flex-1 flex justify-center">
            <Navigation links={showAboutLink ? ['About'] : []} theme={theme} />
          </div>
          
          {/* Right: Yaaralabs.ai */}
          <div className="hidden md:flex items-center gap-2">
            <img 
              src="/yaaralogo.jpg" 
              alt="Yaaralabs.ai Logo" 
              className={`${logoSize === 'sm' ? 'h-6 w-6' : logoSize === 'md' ? 'h-8 w-8' : 'h-10 w-10'} rounded-full`}
            />
            <span className={`font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-800'} ${
              logoSize === 'sm' ? 'text-lg' : logoSize === 'md' ? 'text-xl' : 'text-2xl'
            }`}>
              Yaaralabs.ai
            </span>
          </div>
          
          {/* Mobile menu button */}
          {showMobileMenu && (
            <div className="md:hidden">
              <MobileMenuButton
                isOpen={mobileMenuOpen}
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              />
            </div>
          )}
        </div>

        {/* Mobile menu */}
        {showMobileMenu && (
          <MobileMenu
            isOpen={mobileMenuOpen}
            links={showAboutLink ? ['About'] : []}
          />
        )}
      </nav>
    </header>
  );
}
