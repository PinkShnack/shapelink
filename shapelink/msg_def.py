
"""Definitions for message ids (numeric)"""

message_ids = {
    #: registration
    "MSG_ID_REGISTER": -1,
    #: registration acknowledged
    "MSG_ID_REGISTER_ACK": -2,
    #: end of transmission
    "MSG_ID_EOT": -10,
    #: end of transmission acknowledged
    "MSG_ID_EOT_ACK": -11,
    #: request of feature names from plugin
    "MSG_ID_FEATURE_REQ": -20,
    #: request of feature names from plugin acknowledged
    "MSG_ID_FEATURE_REQ_ACK": -21,

    # other new codes
    "MSG_ps_socket": -40,
    "MSG_ID_feats_code": -50,
    "MSG_ID_feats_code_reply": -51,
    "MSG_ID_params_code": -60,
    "MSG_ID_events_code": -70,
    "MSG_ID_events_code_complete": -71,
    "MSG_ID_end": -80,
    "MSG_ID_end_reply": -81,
}

topicfilter_ids = {"topicfilter_001": b"B"}
