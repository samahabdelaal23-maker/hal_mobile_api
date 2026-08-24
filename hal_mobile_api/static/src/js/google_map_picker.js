/** @odoo-module **/

import {
    Component,
    onMounted,
    onWillUpdateProps,
    useRef,
} from "@odoo/owl";

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";


export class HalGoogleMapPicker extends Component {

    static template = "hal_mobile_api.HalGoogleMapPicker";

    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");

        this.mapContainer = useRef("mapContainer");

        this.map = null;
        this.marker = null;
        this.radiusCircle = null;

        onMounted(async () => {
            await this.loadGoogleMaps();
        });

        onWillUpdateProps((nextProps) => {
            if (!this.map) {
                return;
            }

            const latitude =
                Number(
                    nextProps.record.data.hal_latitude
                ) || 0;

            const longitude =
                Number(
                    nextProps.record.data.hal_longitude
                ) || 0;

            const radius =
                Number(
                    nextProps.record.data.hal_attendance_radius
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
                    radius
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

        // Google Maps already exists on the page.
        if (
            window.google &&
            window.google.maps
        ) {
            this.initializeMap();
            return;
        }

        // Avoid loading the Google Maps script more than once.
        if (window.halGoogleMapsLoadingPromise) {

            try {
                await window.halGoogleMapsLoadingPromise;

                this.initializeMap();

            } catch (error) {
                console.error(error);

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
                        encodeURIComponent(apiKey) +
                        "&v=weekly";

                    script.async = true;
                    script.defer = true;

                    script.onload = () => {
                        resolve();
                    };

                    script.onerror = () => {
                        reject(
                            new Error(
                                "Google Maps script failed to load."
                            )
                        );
                    };

                    document.head.appendChild(
                        script
                    );
                }
            );

        try {
            await window.halGoogleMapsLoadingPromise;

            this.initializeMap();

        } catch (error) {

            console.error(
                "Google Maps loading error:",
                error
            );

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

        const latitude =
            Number(
                record.hal_latitude
            ) || 0;

        const longitude =
            Number(
                record.hal_longitude
            ) || 0;

        const radius =
            Number(
                record.hal_attendance_radius
            ) || 40;

        // -----------------------------------------------------
        // Default location
        //
        // Muscat is used only as the initial map view.
        // Nothing is saved until the administrator clicks
        // an actual location.
        // -----------------------------------------------------

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
            new window.google.maps.Map(
                this.mapContainer.el,
                {
                    center: initialPosition,

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

                    gestureHandling: "greedy",
                }
            );

        // -----------------------------------------------------
        // Existing stored company location
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
        // Admin clicks location on Google Maps
        // -----------------------------------------------------

        this.map.addListener(
            "click",
            async (event) => {

                if (this.props.readonly) {
                    return;
                }

                if (!event.latLng) {
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

                const currentRadius =
                    Number(
                        this.props.record.data
                            .hal_attendance_radius
                    ) || 40;

                this.updateMapPosition(
                    clickedLatitude,
                    clickedLongitude,
                    currentRadius,
                    true,
                );
            }
        );
    }

    // =========================================================
    // SAVE GPS TO CURRENT ODOO RECORD
    // =========================================================

    async saveLocation(
        latitude,
        longitude
    ) {
        await this.props.record.update({
            hal_latitude: latitude,
            hal_longitude: longitude,
        });
    }

    // =========================================================
    // UPDATE MAP POSITION
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

        const lat =
            Number(latitude);

        const lng =
            Number(longitude);

        if (
            !Number.isFinite(lat) ||
            !Number.isFinite(lng)
        ) {
            return;
        }

        const position = {
            lat: lat,
            lng: lng,
        };

        this.createOrMoveMarker(
            lat,
            lng
        );

        this.createOrUpdateCircle(
            lat,
            lng,
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
    // GOOGLE MAPS MARKER
    // =========================================================

    createOrMoveMarker(
        latitude,
        longitude
    ) {

        const position = {
            lat: Number(latitude),
            lng: Number(longitude),
        };

        if (!this.marker) {

            this.marker =
                new window.google.maps.Marker({
                    position: position,

                    map: this.map,

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
    // ATTENDANCE RADIUS CIRCLE
    // =========================================================

    createOrUpdateCircle(
        latitude,
        longitude,
        radius
    ) {

        const center = {
            lat: Number(latitude),
            lng: Number(longitude),
        };

        const radiusValue =
            Number(radius) || 40;

        if (!this.radiusCircle) {

            this.radiusCircle =
                new window.google.maps.Circle({
                    map: this.map,

                    center: center,

                    radius: radiusValue,

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

            this.radiusCircle.setCenter(
                center
            );

            this.radiusCircle.setRadius(
                radiusValue
            );
        }
    }

    // =========================================================
    // CONFIGURATION MESSAGE
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

                    Add the following Odoo system parameter:

                    <br/>

                    <code>
                        hal_mobile_api.google_maps_api_key
                    </code>

                </div>

            </div>
        `;
    }

    // =========================================================
    // MAP LOAD ERROR
    // =========================================================

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

                Please check the Google Maps API key,
                API restrictions and Google Cloud billing.

            </div>
        `;
    }
}


// =============================================================
// REGISTER FIELD WIDGET
// =============================================================

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
