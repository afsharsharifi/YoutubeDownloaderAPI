import re
from typing import Union

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from pytube import YouTube, extract
from starlette.responses import FileResponse

app = FastAPI()

YT_URL_REGEX = "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$"


class Link(BaseModel):
    url: str


class Download(BaseModel):
    url: str
    resolution: str


@app.post("/api/v1/info/")
async def get_video_info(data: Link):
    if not re.match(YT_URL_REGEX, data.url):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="not a valid youtube link")
    url = data.url
    video = YouTube(url)
    video_info = {
        "id": extract.video_id(url),
        "title": video.title,
        "length": video.length,
        "thumbnail_url": video.thumbnail_url,
        "resolutions": [],
    }
    for st in video.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc():
        st_info = {
            "resolution": st.resolution,
            "size": st.filesize,
        }
        video_info["resolutions"].append(st_info)
    return video_info


@app.post("/api/v1/download/")
async def donwload_video(data: Download):
    if not re.match(YT_URL_REGEX, data.url):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="not a valid youtube link")
    url = data.url
    video_id = extract.video_id(url)
    video = YouTube(url)
    video.streams.filter(
        progressive=True,
        file_extension="mp4",
        resolution=data.resolution,
    ).first().download(output_path=f"/download/{video_id}/")
    filename = video.streams.filter(progressive=True, file_extension="mp4", resolution=data.resolution).first().default_filename
    return FileResponse(f"/download/{video_id}/{filename}", media_type="application/octet-stream", filename=filename)
