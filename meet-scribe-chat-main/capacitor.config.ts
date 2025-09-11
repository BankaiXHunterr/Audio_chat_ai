import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'app.lovable.34fe6eac8d164c848ac1eddf61a06f69',
  appName: 'meet-scribe-chat',
  webDir: 'dist',
  server: {
    url: 'https://34fe6eac-8d16-4c84-8ac1-eddf61a06f69.lovableproject.com?forceHideBadge=true',
    cleartext: true
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#FF6600',
      showSpinner: true,
      spinnerColor: '#FFFFFF'
    },
    StatusBar: {
      style: 'LIGHT_CONTENT',
      backgroundColor: '#FF6600'
    }
  }
};

export default config;