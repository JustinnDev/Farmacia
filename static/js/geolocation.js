// Geolocation utilities for FarmaYa

class GeolocationManager {
    constructor() {
        this.userLocation = null;
        this.watchId = null;
    }

    // Get current position
    async getCurrentPosition() {
        console.log('[GeolocationManager] Iniciando getCurrentPosition');
        return new Promise((resolve, reject) => {
            console.log('[GeolocationManager] Verificando soporte de geolocalización');
            if (!navigator.geolocation) {
                console.error('[GeolocationManager] Geolocalización no soportada por el navegador');
                reject(new Error('Geolocation is not supported by this browser'));
                return;
            }
            console.log('[GeolocationManager] Geolocalización soportada, configurando timeout de respaldo');

            // Set a fallback timeout for environments where geolocation might hang
            const fallbackTimeout = setTimeout(() => {
                console.error('[GeolocationManager] Timeout de respaldo activado - rechazando promesa');
                reject(new Error('TIMEOUT'));
            }, 15000); // 15 seconds fallback
            console.log('[GeolocationManager] Timeout de respaldo configurado por 15 segundos');

            console.log('[GeolocationManager] Llamando navigator.geolocation.getCurrentPosition');
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    console.log('[GeolocationManager] Posición obtenida exitosamente:', position.coords);
                    clearTimeout(fallbackTimeout);
                    console.log('[GeolocationManager] Timeout de respaldo limpiado');
                    this.userLocation = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    };
                    console.log('[GeolocationManager] Ubicación del usuario guardada:', this.userLocation);
                    resolve(this.userLocation);
                },
                (error) => {
                    console.error('[GeolocationManager] Error en getCurrentPosition:', error);
                    clearTimeout(fallbackTimeout);
                    console.log('[GeolocationManager] Timeout de respaldo limpiado por error');
                    reject(error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 300000 // 5 minutes
                }
            );
            console.log('[GeolocationManager] navigator.geolocation.getCurrentPosition llamado con opciones');
        });
    }

    // Watch position changes
    watchPosition(callback) {
        console.log('[GeolocationManager] Iniciando watchPosition');
        if (!navigator.geolocation) {
            console.error('[GeolocationManager] Geolocalización no soportada para watchPosition');
            return;
        }
        console.log('[GeolocationManager] Iniciando watchPosition con callback');

        this.watchId = navigator.geolocation.watchPosition(
            (position) => {
                console.log('[GeolocationManager] Nueva posición en watchPosition:', position.coords);
                this.userLocation = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                };
                console.log('[GeolocationManager] Ubicación actualizada en watchPosition:', this.userLocation);
                callback(this.userLocation);
            },
            (error) => {
                console.error('[GeolocationManager] Error en watchPosition:', error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000
            }
        );
        console.log('[GeolocationManager] watchPosition iniciado con ID:', this.watchId);
    }

    // Stop watching position
    stopWatching() {
        console.log('[GeolocationManager] Ejecutando stopWatching, watchId actual:', this.watchId);
        if (this.watchId) {
            navigator.geolocation.clearWatch(this.watchId);
            console.log('[GeolocationManager] clearWatch ejecutado para ID:', this.watchId);
            this.watchId = null;
            console.log('[GeolocationManager] watchId establecido a null');
        } else {
            console.log('[GeolocationManager] No hay watchId activo para detener');
        }
    }

    // Calculate distance between two points using Haversine formula
    static calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth's radius in kilometers
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a =
            Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    // Get user-friendly error message
    static getErrorMessage(error) {
        console.log('[GeolocationManager] Procesando mensaje de error:', error);
        if (error.message === 'TIMEOUT') {
            console.log('[GeolocationManager] Error identificado como timeout personalizado');
            return 'Se agotó el tiempo para obtener la ubicación';
        }
        console.log('[GeolocationManager] Procesando error por código, código:', error.code);
        switch(error.code) {
            case error.PERMISSION_DENIED:
                console.log('[GeolocationManager] Error: Permiso denegado');
                return 'El usuario negó el permiso de ubicación';
            case error.POSITION_UNAVAILABLE:
                console.log('[GeolocationManager] Error: Posición no disponible');
                return 'La ubicación no está disponible';
            case error.TIMEOUT:
                console.log('[GeolocationManager] Error: Timeout del navegador');
                return 'Se agotó el tiempo para obtener la ubicación';
            default:
                console.log('[GeolocationManager] Error desconocido, código:', error.code);
                return 'Error desconocido al obtener la ubicación';
        }
    }
}

// Global instance
console.log('[GeolocationManager] Creando instancia global de GeolocationManager');
const geolocationManager = new GeolocationManager();
console.log('[GeolocationManager] Instancia global creada:', geolocationManager);