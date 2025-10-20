import logging
from typing import List

import numpy as np
import pydantic
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from database import BeaconDetection
from tdoa import tdoa_localization_geodetic


Templates = Jinja2Templates(directory="templates")


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)
logger.setLevel('INFO')


app = FastAPI()


@app.get("/")
def index_page_handler(request: Request):
    return Templates.TemplateResponse(
        request=request, name="index.html", context={},
    )


class DronePositionItemResponse(pydantic.BaseModel):
    lat: float
    lon: float
    drone_id: str
    tdoa: int = 0


class BeaconPositionItemResponse(pydantic.BaseModel):
    lat: float
    lon: float


class BeaconPositionResponse(pydantic.BaseModel):
    beacon: BeaconPositionItemResponse
    drones: List[DronePositionItemResponse]


@app.get("/api/beacon/{beacon_id}")
async def beacon_position_handler(beacon_id):
    logger.info(f'{BeaconDetection} {beacon_id}')

    detections = BeaconDetection.filter_last_detections(beacon_id)

    receivers = [
        [d.receiver_lat, d.receiver_lon]
        for d in detections
    ]
    times = np.array([d.toa * 0.1**9 for d in detections])
    tdoa = times[1:] - times[0]
    estimated = tdoa_localization_geodetic(
        receiver_latlons=receivers,
        time_differences=tdoa,
    )

    logger.info(f"Estimated = {estimated}, receivers={receivers}, tdoa={tdoa}.")

    return BeaconPositionResponse(
        beacon=BeaconPositionItemResponse(
            lat=estimated[0],
            lon=estimated[1],
        ),
        drones=[
            DronePositionItemResponse(
                drone_id=d.receiver_id,
                lat=d.receiver_lat,
                lon=d.receiver_lon,
                tdoa=int(10**9 * (times[n] - times[0])),
            )
            for n, d in enumerate(detections)
        ],
    )
