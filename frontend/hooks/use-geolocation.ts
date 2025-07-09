import { useState, useEffect } from 'react';

interface GeolocationState {
  coordinates: {
    latitude: number;
    longitude: number;
  } | null;
  loading: boolean;
  error: string | null;
}

export const useGeolocation = () => {
  const [state, setState] = useState<GeolocationState>({
    coordinates: null,
    loading: false,
    error: null
  });

  const getCurrentLocation = () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    if (!navigator.geolocation) {
      setState({
        coordinates: null,
        loading: false,
        error: 'Geolocalização não suportada pelo navegador'
      });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setState({
          coordinates: {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          },
          loading: false,
          error: null
        });
      },
      (error) => {
        let errorMessage = 'Erro ao obter localização';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Permissão de localização negada';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Localização indisponível';
            break;
          case error.TIMEOUT:
            errorMessage = 'Tempo esgotado ao obter localização';
            break;
        }
        setState({
          coordinates: null,
          loading: false,
          error: errorMessage
        });
      },
      {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0
      }
    );
  };

  return {
    ...state,
    getCurrentLocation
  };
};