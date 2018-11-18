"""Mostly query constants."""
AWAIR_URL = "https://developer-apis.awair.is/graphql"
USER_QUERY = """
User {
    id
    email
    name {
        firstName
        lastName
    }
    dob {
        year
        month
        day
    }
    sex
    tier
    permissions {
        scope
        quota
    }
    usage {
        scope
        counts
    }
}"""

DEVICE_QUERY = """
Devices {
    devices {
        uuid
        deviceType
        deviceId
        name
        preference
        macAddress
        room {
            id
            name
            kind
            Space {
                id
                kind
                location {
                    name
                    timezone
                    lat
                    lon
                }
            }
        }
    }
}"""

AIR_DATA_SEQ = """
airDataSeq {
    timestamp
    score
    sensors {
        component
        value
    }
    indices {
        component
        value
    }
}
"""

LATEST_QUERY = """
AirDataLatest(%s) {
    %s
}""" % ("%s", AIR_DATA_SEQ)

FIVE_MIN_QUERY = """
AirData5Minute(%s) {
    %s
}""" % ("%s", AIR_DATA_SEQ)

FIFTEEN_MIN_QUERY = """
AirData15Minute(%s) {
    %s
}""" % ("%s", AIR_DATA_SEQ)

RAW_QUERY = """
AirDataRaw(%s) {
    %s
}""" % ("%s", AIR_DATA_SEQ)
