point_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://geojson.org/schema/Point.json",
    "title": "GeoJSON Point",
    "type": "object",
    "required": [
        "type",
        "coordinates"
    ],
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "Point"
            ]
        },
        "coordinates": {
            "type": "array",
            "minItems": 2,
            "items": {
                "type": "number"
            }
        },
        "bbox": {
            "type": "array",
            "minItems": 4,
            "items": {
                "type": "number"
            }
        }
    }
}

linestring_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://geojson.org/schema/LineString.json",
    "title": "GeoJSON LineString",
    "type": "object",
    "required": [
        "type",
        "coordinates"
    ],
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "LineString"
            ]
        },
        "coordinates": {
            "type": "array",
            "minItems": 2,
            "items": {
                "type": "array",
                "minItems": 2,
                "items": {
                    "type": "number"
                }
            }
        },
        "bbox": {
            "type": "array",
            "minItems": 4,
            "items": {
                "type": "number"
            }
        }
    }
}

polygon_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://geojson.org/schema/Polygon.json",
    "title": "GeoJSON Polygon",
    "type": "object",
    "required": [
        "type",
        "coordinates"
    ],
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "Polygon"
            ]
        },
        "coordinates": {
            "type": "array",
            "items": {
                "type": "array",
                "minItems": 4,
                "items": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                        "type": "number"
                    }
                }
            }
        },
        "bbox": {
            "type": "array",
            "minItems": 4,
            "items": {
                "type": "number"
            }
        }
    }
}

multipoint_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://geojson.org/schema/MultiPoint.json",
    "title": "GeoJSON MultiPoint",
    "type": "object",
    "required": [
        "type",
        "coordinates"
    ],
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "MultiPoint"
            ]
        },
        "coordinates": {
            "type": "array",
            "items": {
                "type": "array",
                "minItems": 2,
                "items": {
                    "type": "number"
                }
            }
        },
        "bbox": {
            "type": "array",
            "minItems": 4,
            "items": {
                "type": "number"
            }
        }
    }
}

multilinestring_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://geojson.org/schema/MultiLineString.json",
    "title": "GeoJSON MultiLineString",
    "type": "object",
    "required": [
        "type",
        "coordinates"
    ],
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "MultiLineString"
            ]
        },
        "coordinates": {
            "type": "array",
            "items": {
                "type": "array",
                "minItems": 2,
                "items": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                        "type": "number"
                    }
                }
            }
        },
        "bbox": {
            "type": "array",
            "minItems": 4,
            "items": {
                "type": "number"
            }
        }
    }
}

multipolygon_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://geojson.org/schema/MultiPolygon.json",
    "title": "GeoJSON MultiPolygon",
    "type": "object",
    "required": [
        "type",
        "coordinates"
    ],
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "MultiPolygon"
            ]
        },
        "coordinates": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {
                    "type": "array",
                    "minItems": 4,
                    "items": {
                        "type": "array",
                        "minItems": 2,
                        "items": {
                            "type": "number"
                        }
                    }
                }
            }
        },
        "bbox": {
            "type": "array",
            "minItems": 4,
            "items": {
                "type": "number"
            }
        }
    }
}

geometrycollection_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://geojson.org/schema/GeometryCollection.json",
    "title": "GeoJSON GeometryCollection",
    "type": "object",
    "required": [
        "type",
        "geometries"
    ],
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "GeometryCollection"
            ]
        },
        "geometries": {
            "type": "array",
            "items": {
                "oneOf": [
                    {
                        "title": "GeoJSON Point",
                        "type": "object",
                        "required": [
                            "type",
                            "coordinates"
                        ],
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "Point"
                                ]
                            },
                            "coordinates": {
                                "type": "array",
                                "minItems": 2,
                                "items": {
                                    "type": "number"
                                }
                            },
                            "bbox": {
                                "type": "array",
                                "minItems": 4,
                                "items": {
                                    "type": "number"
                                }
                            }
                        }
                    },
                    {
                        "title": "GeoJSON LineString",
                        "type": "object",
                        "required": [
                            "type",
                            "coordinates"
                        ],
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "LineString"
                                ]
                            },
                            "coordinates": {
                                "type": "array",
                                "minItems": 2,
                                "items": {
                                    "type": "array",
                                    "minItems": 2,
                                    "items": {
                                        "type": "number"
                                    }
                                }
                            },
                            "bbox": {
                                "type": "array",
                                "minItems": 4,
                                "items": {
                                    "type": "number"
                                }
                            }
                        }
                    },
                    {
                        "title": "GeoJSON Polygon",
                        "type": "object",
                        "required": [
                            "type",
                            "coordinates"
                        ],
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "Polygon"
                                ]
                            },
                            "coordinates": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "minItems": 4,
                                    "items": {
                                        "type": "array",
                                        "minItems": 2,
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            },
                            "bbox": {
                                "type": "array",
                                "minItems": 4,
                                "items": {
                                    "type": "number"
                                }
                            }
                        }
                    },
                    {
                        "title": "GeoJSON MultiPoint",
                        "type": "object",
                        "required": [
                            "type",
                            "coordinates"
                        ],
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "MultiPoint"
                                ]
                            },
                            "coordinates": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "minItems": 2,
                                    "items": {
                                        "type": "number"
                                    }
                                }
                            },
                            "bbox": {
                                "type": "array",
                                "minItems": 4,
                                "items": {
                                    "type": "number"
                                }
                            }
                        }
                    },
                    {
                        "title": "GeoJSON MultiLineString",
                        "type": "object",
                        "required": [
                            "type",
                            "coordinates"
                        ],
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "MultiLineString"
                                ]
                            },
                            "coordinates": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "minItems": 2,
                                    "items": {
                                        "type": "array",
                                        "minItems": 2,
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            },
                            "bbox": {
                                "type": "array",
                                "minItems": 4,
                                "items": {
                                    "type": "number"
                                }
                            }
                        }
                    },
                    {
                        "title": "GeoJSON MultiPolygon",
                        "type": "object",
                        "required": [
                            "type",
                            "coordinates"
                        ],
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "MultiPolygon"
                                ]
                            },
                            "coordinates": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "minItems": 4,
                                        "items": {
                                            "type": "array",
                                            "minItems": 2,
                                            "items": {
                                                "type": "number"
                                            }
                                        }
                                    }
                                }
                            },
                            "bbox": {
                                "type": "array",
                                "minItems": 4,
                                "items": {
                                    "type": "number"
                                }
                            }
                        }
                    }
                ]
            }
        },
        "bbox": {
            "type": "array",
            "minItems": 4,
            "items": {
                "type": "number"
            }
        }
    }
}

geometry_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://geojson.org/schema/Geometry.json",
    "title": "GeoJSON Geometry",
    "oneOf": [
        {
            "title": "GeoJSON Point",
            "type": "object",
            "required": [
                "type",
                "coordinates"
            ],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [
                        "Point"
                    ]
                },
                "coordinates": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                        "type": "number"
                    }
                },
                "bbox": {
                    "type": "array",
                    "minItems": 4,
                    "items": {
                        "type": "number"
                    }
                }
            }
        },
        {
            "title": "GeoJSON LineString",
            "type": "object",
            "required": [
                "type",
                "coordinates"
            ],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [
                        "LineString"
                    ]
                },
                "coordinates": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                        "type": "array",
                        "minItems": 2,
                        "items": {
                            "type": "number"
                        }
                    }
                },
                "bbox": {
                    "type": "array",
                    "minItems": 4,
                    "items": {
                        "type": "number"
                    }
                }
            }
        },
        {
            "title": "GeoJSON Polygon",
            "type": "object",
            "required": [
                "type",
                "coordinates"
            ],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [
                        "Polygon"
                    ]
                },
                "coordinates": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "minItems": 4,
                        "items": {
                            "type": "array",
                            "minItems": 2,
                            "items": {
                                "type": "number"
                            }
                        }
                    }
                },
                "bbox": {
                    "type": "array",
                    "minItems": 4,
                    "items": {
                        "type": "number"
                    }
                }
            }
        },
        {
            "title": "GeoJSON MultiPoint",
            "type": "object",
            "required": [
                "type",
                "coordinates"
            ],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [
                        "MultiPoint"
                    ]
                },
                "coordinates": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "minItems": 2,
                        "items": {
                            "type": "number"
                        }
                    }
                },
                "bbox": {
                    "type": "array",
                    "minItems": 4,
                    "items": {
                        "type": "number"
                    }
                }
            }
        },
        {
            "title": "GeoJSON MultiLineString",
            "type": "object",
            "required": [
                "type",
                "coordinates"
            ],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [
                        "MultiLineString"
                    ]
                },
                "coordinates": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "minItems": 2,
                        "items": {
                            "type": "array",
                            "minItems": 2,
                            "items": {
                                "type": "number"
                            }
                        }
                    }
                },
                "bbox": {
                    "type": "array",
                    "minItems": 4,
                    "items": {
                        "type": "number"
                    }
                }
            }
        },
        {
            "title": "GeoJSON MultiPolygon",
            "type": "object",
            "required": [
                "type",
                "coordinates"
            ],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [
                        "MultiPolygon"
                    ]
                },
                "coordinates": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "minItems": 4,
                            "items": {
                                "type": "array",
                                "minItems": 2,
                                "items": {
                                    "type": "number"
                                }
                            }
                        }
                    }
                },
                "bbox": {
                    "type": "array",
                    "minItems": 4,
                    "items": {
                        "type": "number"
                    }
                }
            }
        }
    ]
}

json_schema = {
    "point": point_json_schema,
    "Point": point_json_schema,
    "linestring": linestring_json_schema,
    "LineString": linestring_json_schema,
    "polygon": polygon_json_schema,
    "Polygon": polygon_json_schema,
    "multipoint": multipoint_json_schema,
    "MultiPoint": multipoint_json_schema,
    "multilinestring": multilinestring_json_schema,
    "MultiLineString": multilinestring_json_schema,
    "multipolygon": multipolygon_json_schema,
    "MultiPolygon": multipolygon_json_schema,
    "geometrycollection": geometrycollection_json_schema,
    "GeometryCollection": geometrycollection_json_schema,
    "geometry": geometry_json_schema,
    "Geometry": geometry_json_schema,
}
