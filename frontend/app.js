const INITIAL_CENTER = [28.2, -4.0];
const INITIAL_ZOOM = 9;

let map;
let protocol;

function initMap() {
    protocol = new pmtiles.Protocol();
    maplibregl.addProtocol('pmtiles', protocol.tile);

    map = new maplibregl.Map({
        container: 'map',
        style: {
            version: 8,
            sources: {
                'osm': {
                    type: 'raster',
                    tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                    tileSize: 256,
                    attribution: '© OpenStreetMap contributors'
                }
            },
            layers: [
                {
                    id: 'osm',
                    type: 'raster',
                    source: 'osm',
                    minzoom: 0,
                    maxzoom: 19
                }
            ]
        },
        center: INITIAL_CENTER,
        zoom: INITIAL_ZOOM
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.ScaleControl(), 'bottom-right');

    map.on('load', () => {
        loadLayers();
        setupLayerToggles();
        setupClickHandlers();
    });
}

function loadLayers() {
    const dataPath = '../data/outputs';

    map.addSource('h3-grid', {
        type: 'geojson',
        data: `${dataPath}/h3_grid.geojson`
    });

    map.addSource('facilities', {
        type: 'geojson',
        data: `${dataPath}/health_facilities.geojson`
    });

    map.addLayer({
        id: 'h3-exposure',
        type: 'fill',
        source: 'h3-grid',
        paint: {
            'fill-color': [
                'interpolate',
                ['linear'],
                ['get', 'population_exposed'],
                0, '#f7fbff',
                10, '#deebf7',
                50, '#9ecae1',
                100, '#3182bd',
                200, '#08519c'
            ],
            'fill-opacity': 0.7
        },
        layout: {
            'visibility': 'visible'
        }
    });

    map.addLayer({
        id: 'h3-accessibility',
        type: 'fill',
        source: 'h3-grid',
        paint: {
            'fill-color': [
                'match',
                ['get', 'accessibility_class'],
                'good', '#1a9850',
                'moderate', '#fdae61',
                'poor', '#d73027',
                '#cccccc'
            ],
            'fill-opacity': 0.7
        },
        layout: {
            'visibility': 'none'
        }
    });

    map.addLayer({
        id: 'h3-priority',
        type: 'fill',
        source: 'h3-grid',
        paint: {
            'fill-color': [
                'match',
                ['get', 'priority_class'],
                'high', '#d73027',
                'medium', '#fee090',
                'low', '#4575b4',
                '#e0e0e0'
            ],
            'fill-opacity': 0.8
        },
        layout: {
            'visibility': 'visible'
        }
    });

    map.addLayer({
        id: 'h3-outline',
        type: 'line',
        source: 'h3-grid',
        paint: {
            'line-color': '#ffffff',
            'line-width': 0.5,
            'line-opacity': 0.5
        }
    });

    map.addLayer({
        id: 'facilities',
        type: 'circle',
        source: 'facilities',
        paint: {
            'circle-radius': 8,
            'circle-color': '#e74c3c',
            'circle-stroke-width': 3,
            'circle-stroke-color': '#ffffff'
        },
        layout: {
            'visibility': 'visible'
        }
    });
}

function setupLayerToggles() {
    const toggles = {
        'layer-priority': 'h3-priority',
        'layer-exposure': 'h3-exposure',
        'layer-accessibility': 'h3-accessibility',
        'layer-facilities': 'facilities'
    };

    Object.entries(toggles).forEach(([checkboxId, layerIds]) => {
        const checkbox = document.getElementById(checkboxId);
        if (!checkbox) return;

        checkbox.addEventListener('change', (e) => {
            const visibility = e.target.checked ? 'visible' : 'none';
            const layers = Array.isArray(layerIds) ? layerIds : [layerIds];

            layers.forEach(layerId => {
                if (map.getLayer(layerId)) {
                    map.setLayoutProperty(layerId, 'visibility', visibility);
                }
            });
        });
    });
}

function setupClickHandlers() {
    map.on('click', 'h3-priority', (e) => {
        if (e.features.length > 0) {
            showPopup(e.features[0], e.lngLat);
        }
    });

    map.on('click', 'h3-exposure', (e) => {
        if (e.features.length > 0) {
            showPopup(e.features[0], e.lngLat);
        }
    });

    map.on('click', 'h3-accessibility', (e) => {
        if (e.features.length > 0) {
            showPopup(e.features[0], e.lngLat);
        }
    });

    map.on('click', 'facilities', (e) => {
        if (e.features.length > 0) {
            showFacilityPopup(e.features[0], e.lngLat);
        }
    });

    map.on('mouseenter', 'h3-priority', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'h3-priority', () => {
        map.getCanvas().style.cursor = '';
    });

    map.on('mouseenter', 'h3-exposure', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'h3-exposure', () => {
        map.getCanvas().style.cursor = '';
    });

    map.on('mouseenter', 'h3-accessibility', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'h3-accessibility', () => {
        map.getCanvas().style.cursor = '';
    });

    map.on('mouseenter', 'facilities', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'facilities', () => {
        map.getCanvas().style.cursor = '';
    });

    // Add hover tooltips for facilities
    let facilityPopup = null;

    map.on('mouseenter', 'facilities', (e) => {
        if (e.features.length > 0) {
            const props = e.features[0].properties;
            const coordinates = e.features[0].geometry.coordinates.slice();

            // Create hover tooltip
            facilityPopup = new maplibregl.Popup({
                closeButton: false,
                closeOnClick: false,
                offset: 15
            })
                .setLngLat(coordinates)
                .setHTML(`
                    <div style="font-size: 12px; padding: 4px;">
                        <strong>${props.name || 'Health Facility'}</strong><br>
                        <span style="color: #666;">${props.amenity || 'Healthcare'}</span>
                    </div>
                `)
                .addTo(map);
        }
    });

    map.on('mouseleave', 'facilities', () => {
        if (facilityPopup) {
            facilityPopup.remove();
            facilityPopup = null;
        }
    });
}

function showPopup(feature, lngLat) {
    const props = feature.properties;

    const content = `
        <h4>Hex Statistics</h4>
        <div class="stat">
            <span class="stat-label">Population:</span>
            <span class="stat-value">${Math.round(props.population || 0)}</span>
        </div>
        <div class="stat">
            <span class="stat-label">Exposed:</span>
            <span class="stat-value">${Math.round(props.population_exposed || 0)} (${(props.exposure_pct || 0).toFixed(1)}%)</span>
        </div>
        <div class="stat">
            <span class="stat-label">Nearest Facility:</span>
            <span class="stat-value">${(props.nearest_facility_km || 0).toFixed(2)} km</span>
        </div>
        <div class="stat">
            <span class="stat-label">Accessibility:</span>
            <span class="stat-value">${props.accessibility_class || 'N/A'}</span>
        </div>
        <div class="stat">
            <span class="stat-label">Priority:</span>
            <span class="stat-value">${props.priority_class || 'N/A'} (${(props.priority_score || 0).toFixed(3)})</span>
        </div>
    `;

    new maplibregl.Popup()
        .setLngLat(lngLat)
        .setHTML(content)
        .addTo(map);
}

function showFacilityPopup(feature, lngLat) {
    const props = feature.properties;

    const content = `
        <h4>Health Facility</h4>
        <div class="stat">
            <span class="stat-label">Name:</span>
            <span class="stat-value">${props.name || 'Unnamed'}</span>
        </div>
        <div class="stat">
            <span class="stat-label">Type:</span>
            <span class="stat-value">${props.amenity || 'Health facility'}</span>
        </div>
    `;

    new maplibregl.Popup()
        .setLngLat(lngLat)
        .setHTML(content)
        .addTo(map);
}

function closePopup() {
    document.getElementById('popup').classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', initMap);
