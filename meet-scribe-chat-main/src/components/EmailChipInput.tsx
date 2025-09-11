import { useState, KeyboardEvent, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { X } from 'lucide-react';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/hooks/useAuth';

interface EmailChipInputProps {
  emails: string[];
  onChange: (emails: string[]) => void;
  placeholder?: string;
  label?: string;
  required?: boolean;
}

export const EmailChipInput = ({ 
  emails, 
  onChange, 
  placeholder = "Enter email addresses...",
  label,
  required = false
}: EmailChipInputProps) => {
  const {user} = useAuth();
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState('');


    // 4. Use useEffect to add the user's email by default
  useEffect(() => {
    // Only run this if there is a logged-in user, and the emails list is empty
    if (user?.email && emails.length === 0) {
      onChange([user.email]);
    }
  }, [user, emails.length, onChange]); // Dependencies for the effect

  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email.trim());
  };

  const addEmail = (email: string) => {
    const trimmedEmail = email.trim().toLowerCase();
    
    if (!trimmedEmail) return;
    
    if (!isValidEmail(trimmedEmail)) {
      setError('Please enter a valid email address');
      return;
    }
    
    if (emails.includes(trimmedEmail)) {
      setError('This email has already been added');
      return;
    }
    
    onChange([...emails, trimmedEmail]);
    setInputValue('');
    setError('');
  };

  const removeEmail = (emailToRemove: string) => {
    onChange(emails.filter(email => email !== emailToRemove));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',' || e.key === ' ') {
      e.preventDefault();
      addEmail(inputValue);
    } else if (e.key === 'Backspace' && !inputValue && emails.length > 0) {
      removeEmail(emails[emails.length - 1]);
    }
  };

  const handleBlur = () => {
    if (inputValue.trim()) {
      addEmail(inputValue);
    }
  };

  return (
    <div className="space-y-2">
      {label && (
        <Label className="text-sm font-medium">
          {label} {required && <span className="text-destructive">*</span>}
        </Label>
      )}
      
      <div className="min-h-[42px] w-full rounded-md border border-input bg-background px-3 py-2 focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2">
        <div className="flex flex-wrap gap-2 mb-2">
          {emails.map((email, index) => (
            <Badge
              key={index}
              variant="secondary"
              className="flex items-center gap-1 px-2 py-1 text-xs font-medium bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
            >
              {email}
              <button
                type="button"
                onClick={() => removeEmail(email)}
                className="ml-1 hover:bg-primary/30 rounded-full p-0.5 transition-colors"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
        
        <Input
          type="email"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setError('');
          }}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          placeholder={emails.length === 0 ? placeholder : "Add another email..."}
          className="border-none p-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-sm"
        />
      </div>
      
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
      
      <p className="text-xs text-muted-foreground">
        Press Enter, comma, or space to add an email. The first email should be yours.
      </p>
    </div>
  );
};