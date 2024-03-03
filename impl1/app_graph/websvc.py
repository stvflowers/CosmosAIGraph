import json
import logging
import os
import time
import traceback

from dotenv import load_dotenv

from fastapi import FastAPI, Request, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Pydantic models defining the "shapes" of requests and responses
from pysrc.models.webservice_models import PingModel
from pysrc.models.webservice_models import LivenessModel
from pysrc.models.webservice_models import OwlInfoModel
from pysrc.models.webservice_models import SparqlQueryRequestModel
from pysrc.models.webservice_models import SparqlQueryResponseModel
from pysrc.models.webservice_models import SparqlBomQueryRequestModel
from pysrc.models.webservice_models import SparqlBomQueryResponseModel

# Services with Business Logic
from pysrc.services.config_service import ConfigService
from pysrc.services.graph_service import GraphService
from pysrc.services.logging_level_service import LoggingLevelService

# standard initialization
load_dotenv(override=True)
logging.basicConfig(
    format="%(asctime)s - %(message)s", level=LoggingLevelService.get_level()
)
ConfigService.log_defined_env_vars()

app = FastAPI()
opts = {}
gs = GraphService(opts)


@app.get("/")
async def get_index() -> PingModel:
    resp = dict()
    resp["epoch"] = str(time.time())
    return resp


@app.get("/liveness")
async def get_liveness(req: Request, resp: Response) -> LivenessModel:
    """
    Return a LivenessModel indicating the health of this microservice.
    This endpoint is invoked by the Azure Container Apps (ACA) service.
    The implementation invokes the liveness_check() method on the
    GraphService object to check that the graph is populated in-memory.
    """
    # See https://learn.microsoft.com/en-us/azure/container-apps/health-probes
    global gs
    liveness_data = dict()
    liveness_data["alive"] = False
    liveness_data["rows_read"] = -1
    liveness_data["epoch"] = time.time()
    try:
        liveness_data = gs.liveness_check()
    except:
        pass
    if liveness_data["alive"] == True:
        resp.status_code = status.HTTP_200_OK
    else:
        resp.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    logging.info("liveness_check: {}".format(liveness_data))
    return liveness_data


@app.get("/owl_info")
async def get_owl_info() -> OwlInfoModel:
    global gs
    owl_info = gs.owl_info()
    owl_info["epoch"] = time.time()
    return owl_info


@app.post("/sparql_query")
async def post_sparql_query(
    req_model: SparqlQueryRequestModel,
) -> SparqlQueryResponseModel:
    global gs
    resp_obj = dict()
    resp_obj["sparql"] = "??"
    resp_obj["results"] = None
    resp_obj["elapsed"] = -1.0
    resp_obj["error"] = None
    t1 = time.perf_counter()
    try:
        resp_obj["sparql"] = req_model.sparql
        rqr = gs.query(req_model.sparql)  # returns a RdfQueryResult object
        rqr.prune_data()
        resp_obj["results"] = rqr.get_data()
    except Exception as e:
        resp_obj["error"] = str(e)
        logging.critical((str(e)))
        print(traceback.format_exc())

    resp_obj["elapsed"] = time.perf_counter() - t1
    # print("post_sparql_query: {}".format(json.dumps(resp_obj)))
    return resp_obj


@app.post("/sparql_bom_query")
async def post_sparql_bom_query(
    req_model: SparqlBomQueryRequestModel,
) -> SparqlBomQueryResponseModel:
    global gs
    resp_obj = dict()
    resp_obj["libtype"] = "?"
    resp_obj["libname"] = "?"
    resp_obj["max_depth"] = -1
    resp_obj["actual_depth"] = -1
    resp_obj["bom_libs"] = None
    resp_obj["elapsed"] = -1.0
    resp_obj["error"] = None
    t1 = time.perf_counter()
    try:
        libtype = req_model.libtype
        libname = req_model.libname
        max_depth = int(req_model.max_depth)
        bqr = gs.bom_query(
            libtype, libname, max_depth
        )  # returns a BomQueryResult object
        resp_obj["libtype"] = libtype
        resp_obj["libname"] = libname
        resp_obj["max_depth"] = max_depth
        resp_obj["actual_depth"] = bqr.get_actual_depth()
        resp_obj["bom_libs"] = bqr.get_bom_libs()
    except Exception as e:
        resp_obj["error"] = str(e)
        logging.critical((str(e)))
        print(traceback.format_exc())

    resp_obj["elapsed"] = time.perf_counter() - t1
    # print("sparql_bom_query: {}".format(json.dumps(resp_obj)))
    return resp_obj
