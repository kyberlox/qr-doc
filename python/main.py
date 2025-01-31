from fastapi import FastAPI, Body, Response, Cookie, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

import qrcode
import zipfile
import os
import io

import datetime

import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

from dotenv import dotenv_values



client = MongoClient("mongodb://mongodb:27017/")

db = client['mongodb']
DirCollection = db['dir-collection']
FileCollection = db['file-collection']
QRCollection = db['qr-collection']



app = FastAPI()

link = os.getenv("project")

origins = [
    "http://localhost:8000",
    "http://localhost:5173",
    f"http://{link}"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT", "OPTIONS", "PATH"],
    allow_headers=["Content-Type", "Accept", "Location", "Allow", "Content-Disposition", "Sec-Fetch-Dest"],
)



@app.get("/api/test/")
def test():
    dir_data = {
        "name" : "test",
        "qr_path" : "",
        "date" : str(datetime.datetime.now().date()),
        "files_id" : []
    }
    dir_id = DirCollection.insert_one(dir_data).insert_id

    return {"dir_id" : dir_id}

@app.get("/api/QR/{num}", response_class = FileResponse)
def getQR(num):
    img = qrcode.make(f'ТУ-{num}...')
    img.save(f"./public/QR_{num}.png")
    return File(f"./public/QR_{num}.png")

@app.get("/api/QRtest/{num}", response_class = FileResponse)
def getQR(num):
    img = qrcode.make(f'ТУ-{num}...')
    img.save(f"./public/QR_{num}.png")
    return FileResponse(f"./public/QR_{num}.png")



#Cоздать директорию
@app.post("/api/dir/", tags=["Dir Methods"])
def post_dir(data = Body()):
    dir_data = {
        "name" : data['name'],
        "qr_path" : "",
        "date" : str(datetime.datetime.now().date()),
        "files_id" : []
    }
    dir_id = DirCollection.insert_one(dir_data).insert_id

    return {"dir_id" : dir_id}

#Просмотьр директориЙ
@app.get("/api/dir/", tags=["Dir Methods"])
def get_dir():
    return DirCollection.find()

#Просмотьр директориИ
@app.get("/api/dir/{ID}", tags=["Dir Methods"])
def get_dir(ID):
    return DirCollection.find_one({"_id": ID})
    #return DirCollection.find_one({"_id": ObjectId(ID)})

#Скачать все файлы из папки zip-фрхивом
def zipfiles(filenames : list, zip_name : str):
    zip_filename = f"{zip_name}.zip"
    s = io.BytesIO()
    zf = zipfile.ZipFile(s, "w")
    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        # Add file, at correct path
        zf.write(fpath, fname)
    # Must close zip for all contents to be written
    zf.close()
    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = Response(s.getvalue(), media_type="application/x-zip-compressed", headers={
        'Content-Disposition': f'attachment;filename={zip_filename}'
    })
    return resp

@app.get("/api/dir/download/{ID}", tags=["Dir Methods"])
def get_dir(ID):
    
    #получить список файлов в папке
    cur_dir = DirCollection.find_one({"_id" : ID})
    files_id = cur_dir[u"files_id"]
    dir_name = cur_dir[u"name"]

    #получить все пути к файлам
    files_path = []
    for fl_id in files_id:
        fl = FileCollection.find_one({'_id' : fl_id})
        fl_path = fl[u"file_path"]
        files_path.append(fl_path)

    return zipfiles(files_path, dir_name)

#Сгенерировать qr-code
@app.put("/api/dir/{ID}", tags=["Dir Methods"])
def put_dir(ID):
    
    #создать ссылку на него
    url = f"hppt://{link}/api/dir/download/{ID}"
    
    #создаем qr-код с ссылкой
    img = qrcode.make(url)
    qr_path = f"./public/QR_dir_{ID}.png"
    img.save(qr_path)

    #обновить данные в файле
    FileCollection.update(
        {'_id' : ID}, 
        {
            '$set' : {
                "qr_path" : qr_path
            }
        }
        )
    
    qr_data = {
        "name" : f"QR_dir_{ID}",
        "path" : qr_path,
        "date" : datetime.datetime.now().date()
    }

    QRCollection.insert_one(qr_data)

    return FileResponse(qr_path)

#Удалить папку
@app.delete("/api/dir/{ID}", tags=["Dir Methods"])
def del_dir(ID):
    return DirCollection.delete_one({"_id": ID})




#Загрузить файд
@app.post("/api/file/", tags=["File Methods"])
def post_file(file: UploadFile):
    #сохранить файл
    file_data = file.file.read()
    f = open(f"./public/{file.filename}", 'wb')
    f.write(file_data)
    f.close()

    file_data = {
        "name" : file.filename,
        "file_path" : f"./public/{file.filename}",
        "qr_path" : "",
        "date" : datetime.datetime.now().date()
    }

    file.file.close()
    file_id = FileCollection.insert_one(file_data).insert_id

    return {"file_id" : file_id}

#Просмотр файла
@app.get("/api/file/{ID}", tags=["File Methods"])
def get_file(ID):
    return DirCollection.find_one({"_id": ID})

#Скачать файл
@app.get("/api/file/download/{ID}", tags=["File Methods"])
def get_file(ID):
    fl = DirCollection.find_one({"_id": ID})
    fl_path = fl[u"file_path"]
    fl_name = fl[u"name"]
    return FileResponse(path=fl_path, filename = fl_name)

#Добавить файл в папку
@app.put("/api/file/dir/{file_id}/{dir_id}", tags=["File Methods"])
def put_file_to_dir(file_id, dir_id):
    #указать его в Папке
    
    #получить список файлов в папке
    cur_dir = DirCollection.find_one({"_id" : dir_id})
    files_id = cur_dir[u"files_id"]

    #добавить файл в папку
    files_id.append(file_id)

    #сделать запись
    DirCollection.update(
        {'_id' : dir_id},
        {
            '$set' : {
                'files_id' : files_id
            }
        }
    )

    return True

#Сгенерировать qr-код 
@app.put("/api/file/{ID}", tags=["File Methods"])
def put_file(ID):
    
    #создать ссылку на него
    url = f"hppt://{link}/api/file/download/{ID}"
    
    #создаем qr-код с ссылкой
    img = qrcode.make(url)
    qr_path = f"./public/QR_file_{ID}.png"
    img.save(qr_path)

    #обновить данные в файле
    FileCollection.update(
        {'_id' : ID}, 
        {
            '$set' : {
                "qr_path" : qr_path
            }
        }
        )
    
    qr_data = {
        "name" : f"QR_file_{ID}",
        "path" : qr_path,
        "date" : datetime.datetime.now().date()
    }

    QRCollection.insert_one(qr_data)

    return FileResponse(qr_path)

#Удалить файл
@app.delete("/api/file/{ID}", tags=["File Methods"])
def del_file(ID):
    return FileCollection.delete_one({"_id": ID})
