import sys

import fitz
import json

from stamp import stamp_recognize, titul_recgnize, reader
from line import linecrop

import cv2 as cv
import numpy as np

with open("config_tmp1.json", "r") as json_file:
    tmp1conf = json.load(json_file)


def get_cropped_image(image, x, y, w, h):
    cropped_image = image[y:h, x:w]
    return cropped_image


def stage():
    pass


# allfileres = {1:{}, 2:{}}
# dodo = [[1,2], [2,3], [3,4], [4,2], [5,2], [6,5], [7,0]]
# for pp, do in zip([1,1,1,1,1,1,1,2,2,2,2,2,2,2,2], [1,2,3,4,5,6,7,1,2,3,4,5,6,7,8]) : #pp, do in zip([1,1,1,1,1,1,1,2,2,2,2,2,2,2,2], [1,2,3,4,5,6,7,1,2,3,4,5,6,7,8])
def ocr(path):
    # doc = fitz.open("template/tmp{}/{}.pdf".format(pp,do))
    doc = fitz.open(path)
    ocr_count = 0
    cp = 0
    titulres = {}
    allres_stamp = []
    for page in doc:
        result_stamp = {'stage': {'easy': "", 'fitz': "", 'tess': ""},
                        'stageSecond': {'easy': "", 'fitz': "", 'tess': ""},
                        'documentDate': {'easy': "",
                                         'fitz': "",
                                         'tess': ""},
                        'documentDateSecond': {'easy': "", 'fitz': "", 'tess': ""},
                        'documentDateThird': {'easy': "", 'fitz': "", 'tess': ""},
                        'changeNumber': {'easy': "",
                                         'fitz': "",
                                         'tess': ""},
                        'designInstitute': {'easy': "",
                                            'fitz': "",
                                            'tess': ""}}
        bb = []
        mat = fitz.Matrix(6, 6)
        rect = page.rect  # the page rectangle
        mp = (rect.tl + rect.br) / 2  # its middle point, becomes top-left of clip
        fitz.Point(0, rect.height / 3)
        # print(mp)

        blocks = page.get_text("dict", flags=0)["blocks"]
        if page.number == 0:
            mp1 = fitz.Point(0, 100)
            mp2 = fitz.Point(rect.width, rect.height - 300)
            clip = fitz.Rect(mp1, mp2)  # the area we want
            # print(clip)
            pix = page.get_pixmap(matrix=mat)  # , clip=clip
            # pix = page.get_pixmap()  # render page to an image
            pix.save("image/page-first-%i.jpg" % page.number)  # store image as a PNG
            titulres = titul_recgnize("image/page-first-%i.jpg" % page.number, tmp1conf["titular"], blocks)
        pix = page.get_pixmap()
        pix.save("image/line.jpg")
        y2, x2 = linecrop("image/line.jpg")

        print(y2)
        print(x2)
        print(rect)
        mediabox = page.mediabox
        w = rect.width - 400
        h = rect.height - 200
        mp1 = fitz.Point(w, h)
        mp2 = fitz.Point(x2 + 1, y2 + 1)
        r = fitz.Rect(0, 0, mediabox.width, x2)
        clip = fitz.Rect(mp1, mp2)  # the area we want

        # print(clip)
        pix = page.get_pixmap(matrix=mat, clip=clip)
        blocks = page.get_text("dict", flags=0, clip=clip)["blocks"]

        filename = "image/page-table-%i.jpg" % page.number

        try:
            pix.save(filename)  # store image as a PNG
            img = cv.imread(cv.samples.findFile(filename))
            cImage = np.copy(img)  # image to draw lines

            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            cv.imwrite(filename, gray)
            easy = reader.readtext(gray)
            # print(easy)
            stageSec = None
            dateSec = None
            for ea in easy:
                if ea[1].lower().strip() == "дата":
                    dateSec = [[ea[0][0][0], ea[0][2][1]],
                               [ea[0][1][0], ea[0][2][1] + (ea[0][2][1] - ea[0][0][1]) + 10]]
                if ea[1].lower().strip() == "стадия":
                    stageSec = [[ea[0][0][0], ea[0][2][1]],
                                [ea[0][1][0], ea[0][2][1] + (ea[0][2][1] - ea[0][0][1]) + 10]]

            for par in tmp1conf["table"]:

                alt_par = None
                if par == "stageSecond" and stageSec is not None:
                    alt_par = stageSec
                elif par == "documentDateSecond" and dateSec is not None:
                    alt_par = dateSec
                if alt_par:
                    tmpar = alt_par
                else:
                    tmpar = tmp1conf["table"][par]["rect"]

                cropped_img = get_cropped_image(gray, tmpar[0][0], tmpar[0][1], tmpar[1][0], tmpar[1][1])
                try:

                    result_stamp[par] = stamp_recognize(cropped_img, tmp1conf["table"][par], par, w, h, alt_par, blocks)

                except Exception as e:
                    print(e)
                cv.imwrite("cropped_img/{}.jpg".format(par), cropped_img)
                # print(par)

        except Exception as e:
            print(e)
        allres_stamp.append(result_stamp)
        cp += 1
        if cp >= 7:
            break
    maxs = 0
    stamp_res = allres_stamp[0]
    for s in allres_stamp:
        size = 0
        for i in s:
            for j in s[i]:
                if s[i][j]:
                    size += 1
                    break
        if maxs < size:
            maxs = size
            stamp_res = s
    print({"stamp": stamp_res, "titul": titulres})
    return {"stamp": stamp_res, "titul": titulres}
