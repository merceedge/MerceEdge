# coding: utf-8
"""Constants used by Merce Edge components."""

__version__ = "0.0.1"
REQUIRED_PYTHON_VER = (3, 4)

# Can be used to specify a catch all when registering state or event listeners.
MATCH_ALL = '*'


# #### EVENTS ####
EVENT_TIME_CHANGED = "time_changed"
EVENT_CALL_SERVICE = "call_service"
EVENT_SERVICE_REGISTERED = "service_registered"
EVENT_STATE_CHANGED = "state_changed"
EVENT_SERVICE_EXECUTED = "service_executed"


# #### STATE AND EVENT ATTRIBUTES ####
# Contains current time for a TIME_CHANGED event
ATTR_NOW = "now"

# Contains domain, service for a SERVICE_CALL event
ATTR_DOMAIN = "domain"
ATTR_SERVICE = "service"
ATTR_SERVICE_DATA = "service_data"

# Data for a SERVICE_EXECUTED event
ATTR_SERVICE_CALL_ID = "service_call_id"

# Contains one string or a list of strings, each being an entity id
ATTR_ENTITY_ID = 'entity_id'

# String with a friendly name for the entity
ATTR_FRIENDLY_NAME = "friendly_name"

# A picture to represent entity
ATTR_ENTITY_PICTURE = "entity_picture"

# Icon to use in the frontend
ATTR_ICON = "icon"

# The unit of measurement if applicable
ATTR_UNIT_OF_MEASUREMENT = "unit_of_measurement"

# Temperature attribute
ATTR_TEMPERATURE = "temperature"
TEMP_CELCIUS = "°C"
TEMP_FAHRENHEIT = "°F"

# Contains the information that is discovered
ATTR_DISCOVERED = "discovered"

# Location of the device/sensor
ATTR_LOCATION = "location"

ATTR_BATTERY_LEVEL = "battery_level"

# For devices which support an armed state
ATTR_ARMED = "device_armed"

# For devices which support a locked state
ATTR_LOCKED = "locked"

# For sensors that support 'tripping', eg. motion and door sensors
ATTR_TRIPPED = "device_tripped"

# For sensors that support 'tripping' this holds the most recent
# time the device was tripped
ATTR_LAST_TRIP_TIME = "last_tripped_time"

# For all entity's, this hold whether or not it should be hidden
ATTR_HIDDEN = "hidden"

# Location of the entity
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"

# Accuracy of location in meters
ATTR_GPS_ACCURACY = 'gps_accuracy'

# If state is assumed
ATTR_ASSUMED_STATE = 'assumed_state'