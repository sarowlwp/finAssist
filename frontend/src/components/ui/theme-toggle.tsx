'use client'

import { useTheme } from '@/components/providers/theme-provider'
import { Button } from '@/components/ui/button'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
      className="w-9 px-0"
    >
      <span className="text-lg">{theme === 'light' ? '🌙' : '☀️'}</span>
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}
