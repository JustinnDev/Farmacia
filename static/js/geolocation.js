// Geolocation utilities for FarmaYa

class GeolocationManager {
    constructor() {
        this.userLocation = null;
        this.watchId = null;
    }

    // Get current position
    async getCurrentPosition() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation is not supported by this browser'));
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.userLocation = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    };
                    resolve(this.userLocation);
                },
                (error) => {
                    reject(error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 300000 // 5 minutes
                }
            );
        });
    }

    // Watch position changes
    watchPosition(callback) {
        if (!navigator.geolocation) {
            console.error('Geolocation is not supported');
            return;
        }

        this.watchId = navigator.geolocation.watchPosition(
            (position) => {
                this.userLocation = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                };
                callback(this.userLocation);
            },
            (error) => {
                console.error('Error watching position:', error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000
            }
        );
    }

    // Stop watching position
    stopWatching() {
        if (this.watchId) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
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
        switch(error.code) {
            case error.PERMISSION_DENIED:
                return 'El usuario negó el permiso de ubicación';
            case error.POSITION_UNAVAILABLE:
                return 'La ubicación no está disponible';
            case error.TIMEOUT:
                return 'Se agotó el tiempo para obtener la ubicación';
            default:
                return 'Error desconocido al obtener la ubicación';
        }
    }
}

// Global instance
const geolocationManager = new GeolocationManager();