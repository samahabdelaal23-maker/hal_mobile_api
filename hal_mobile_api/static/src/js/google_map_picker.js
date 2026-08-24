/** @odoo-module **/

import {
    Component,
    onMounted,
    onWillUpdateProps,
    useRef,
} from "@odoo/owl";

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

import {
    standardFieldProps,
} from "@web/views/fields/standard_field_props";


export class HalGoogleMapPicker extends Component {

    static template =
        "hal_mobile_api.HalGoogleMapPicker";

    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");

        this.mapContainer =
            useRef("mapContainer");

        this.map = null;
        this.marker = null;
        this.radiusCircle = null;

        this.googleMapsLoaded = false;

        onMounted(async () => {
            await this.loadGoogleMaps();
        });

        onWillUpdateProps((nextProps) => {
            if (!this.map) {
                return;
            }

            const latitude =
                Number(
                    nextProps.record.data
                        .hal_latitude
                ) || 0;

            const longitude =
                Number(
                    nextProps.record.data
                        .hal_longitude
                ) || 0;

            const radius =
                Number(
                    nextProps.record.data
                        .hal_attendance_radius
                ) || 40;

            if (
                latitude !== 0 ||
                longitude !== 0
            ) {
                this.updateMapPosition(
                    latitude,
                    longitude,
                    radius,
                    false,
                );
            }

            if (this.radiusCircle) {
                this.radiusCircle.setRadius(
                    radius,
                );
            }
        });
    }

    // =========================================================
    // GOOGLE MAPS LOADER
    // =========================================================

    async loadGoogleMaps() {

        let apiKey = "";

        try {
            apiKey = await this.orm.call(
                "hr.work.location",
                "get_hal_google_maps_api_key",
                [],
            );
        } catch (error) {
            console.error(
                "Could not read Google Maps API key:",
                error
            );
        }

        if (!apiKey) {
            this.showConfigurationMessage();
            return;
        }

        // Google Maps already loaded by another widget/page.
        if (
            window.google &&
            window.google.maps
        ) {
            this.googleMapsLoaded = true;
            this.initializeMap();
            return;
        }

        // Prevent loading the Google script multiple times.
        if (
            window
                .halGoogleMapsLoadingPromise
        ) {
            try {
                await window
                    .halGoogleMapsLoadingPromise;

                this.googleMapsLoaded = true;
                this.initializeMap();
            } catch (error) {
                this.showLoadError();
            }

            return;
        }

        window.halGoogleMapsLoadingPromise =
            new Promise(
                (resolve, reject) => {

                    const script =
                        document.createElement(
                            "script"
                        );

                    script.src =
                        "https://maps.googleapis.com/maps/api/js" +
                        "?key=" +
                        encodeURIComponent(
                            apiKey
                        ) +
                        "&v=weekly";

                    script.async = true;
                    script.defer = true;

                    script.onload =
                        () => resolve();

                    script.onerror =
                        () => reject(
                            new Error(
                                "Google Maps script failed to load."
                            )
                        );

                    document.head
                        .appendChild(
                            script
                        );
                }
            );

        try {
            await window
                .halGoogleMapsLoadingPromise;

            this.googleMapsLoaded = true;

            this.initializeMap();

        } catch (error) {
            console.error(error);

            this.showLoadError();
        }
    }

    // =========================================================
    // INITIALIZE MAP
    // =========================================================

    initializeMap() {

        if (
            !this.mapContainer.el ||
            !window.google ||
            !window.google.maps
        ) {
            return;
        }

        const record =
            this.props.record.data;

        let latitude =
            Number(
                record.hal_latitude
            ) || 0;

        let longitude =
            Number(
                record.hal_longitude
            ) || 0;

        const radius =
            Number(
                record.hal_attendance_radius
            ) || 40;

        // Default view = Muscat.
        // This is ONLY the initial visual center.
        // It is not saved until the admin selects a location.
        let initialPosition;

        if (
            latitude !== 0 ||
            longitude !== 0
        ) {

            initialPosition = {
                lat: latitude,
                lng: longitude,
            };

        } else {

            initialPosition = {
                lat: 23.5880,
                lng: 58.3829,
            };
        }

        this.map =
            new google.maps.Map(
                this.mapContainer.el,
                {
                    center:
                        initialPosition,

                    zoom:
                        (
                            latitude !== 0 ||
                            longitude !== 0
                        )
                            ? 18
                            : 12,

                    mapTypeControl: true,

                    streetViewControl: false,

                    fullscreenControl: true,
                }
            );

        // -----------------------------------------------------
        // Existing saved location
        // -----------------------------------------------------

        if (
            latitude !== 0 ||
            longitude !== 0
        ) {
            this.createOrMoveMarker(
                latitude,
                longitude
            );

            this.createOrUpdateCircle(
                latitude,
                longitude,
                radius
            );
        }

        // -----------------------------------------------------
        // Select location by clicking map
        // -----------------------------------------------------

        this.map.addListener(
            "click",
            async (event) => {

                if (
                    this.props.readonly
                ) {
                    return;
                }

                const clickedLatitude =
                    event.latLng.lat();

                const clickedLongitude =
                    event.latLng.lng();

                await this.saveLocation(
                    clickedLatitude,
                    clickedLongitude
                );

                this.updateMapPosition(
                    clickedLatitude,
                    clickedLongitude,
                    radius,
                    true,
                );
            }
        );
    }

    // =========================================================
    // SAVE LATITUDE / LONGITUDE TO ODOO RECORD
    // =========================================================

    async saveLocation(
        latitude,
        longitude
    ) {

        await this.props.record.update({
            hal_latitude:
                latitude,

            hal_longitude:
                longitude,
        });
    }

    // =========================================================
    // UPDATE MAP
    // =========================================================

    updateMapPosition(
        latitude,
        longitude,
        radius,
        recenter = true,
    ) {

        if (!this.map) {
            return;
        }

        const position = {
            lat:
                Number(latitude),

            lng:
                Number(longitude),
        };

        this.createOrMoveMarker(
            position.lat,
            position.lng
        );

        this.createOrUpdateCircle(
            position.lat,
            position.lng,
            radius
        );

        if (recenter) {
            this.map.panTo(
                position
            );

            this.map.setZoom(
                18
            );
        }
    }

    // =========================================================
    // MARKER
    // =========================================================

    createOrMoveMarker(
        latitude,
        longitude
    ) {

        const position = {
            lat:
                latitude,

            lng:
                longitude,
        };

        if (!this.marker) {

            this.marker =
                new google.maps.Marker({
                    position:
                        position,

                    map:
                        this.map,

                    title:
                        "HAL Work Location",
                });

        } else {

            this.marker.setPosition(
                position
            );
        }
    }

    // =========================================================
    // ALLOWED RADIUS
    // =========================================================

    createOrUpdateCircle(
        latitude,
        longitude,
        radius
    ) {

        const center = {
            lat:
                latitude,

            lng:
                longitude,
        };

        if (!this.radiusCircle) {

            this.radiusCircle =
                new google.maps.Circle({
                    map:
                        this.map,

                    center:
                        center,

                    radius:
                        Number(radius) || 40,

                    strokeColor:
                        "#159BBE",

                    strokeOpacity:
                        0.85,

                    strokeWeight:
                        2,

                    fillColor:
                        "#29E5FF",

                    fillOpacity:
                        0.16,

                    clickable:
                        false,
                });

        } else {

            this.radiusCircle
                .setCenter(
                    center
                );

            this.radiusCircle
                .setRadius(
                    Number(radius) ||
                    40
                );
        }
    }

    // =========================================================
    // MESSAGES
    // =========================================================

    showConfigurationMessage() {

        if (!this.mapContainer.el) {
            return;
        }

        this.mapContainer.el.innerHTML = `
            <div class="hal_map_message">
                <span class="fa fa-map-marker"/>
                <div>
                    <strong>
                        Google Maps API key is not configured.
                    </strong>
                    <br/>
                    Add the system parameter:
                    <code>
                        hal_mobile_api.google_maps_api_key
                    </code>
                </div>
            </div>
        `;
    }

    showLoadError() {

        if (!this.mapContainer.el) {
            return;
        }

        this.mapContainer.el.innerHTML = `
            <div class="hal_map_message hal_map_error">
                <strong>
                    Google Maps could not be loaded.
                </strong>
                <br/>
                Check the API key,
                Google Cloud restrictions,
                and billing configuration.
            </div>
        `;
    }
}


HalGoogleMapPicker.template = `
    <div class="hal_google_map_picker">

        <div class="hal_map_header">

            <div>
                <strong>
                    Google Maps Work Location
                </strong>

                <div class="text-muted">
                    Click the exact company location on the map.
                    The blue circle represents the allowed
                    attendance radius.
                </div>
            </div>

        </div>

        <div
            class="hal_google_map_container"
            t-ref="mapContainer"
        />

    </div>
`;


registry
    .category("fields")
    .add(
        "hal_google_map_picker",
        {
            component:
                HalGoogleMapPicker,

            supportedTypes: [
                "float",
            ],
        }
    );
