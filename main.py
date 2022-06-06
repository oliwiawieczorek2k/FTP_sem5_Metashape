import Metashape
import os

doc = Metashape.app.document
output = Metashape.app.getExistingDirectory('folder do wyników')


def wczytanie_zdjec():
    folder_zdj = Metashape.app.getExistingDirectory('folder ze zdjęciami')
    zdjecia = [os.path.join(folder_zdj, file) for file in os.listdir(folder_zdj) if file.endswith('JPG')]
    chunk1 = doc.chunk
    chunk2 = doc.addChunk()
    chunk1.addPhotos(zdjecia[:len(zdjecia) // 2])
    chunk2.addPhotos(zdjecia[len(zdjecia) // 2:])
    doc.save(output + '/fotoProjekt1.psx')


def orientacja_zdjec():
    for chunk in doc.chunks:
        for frame in chunk.frames:
            frame.matchPhotos(downscale=8)  # lowest?
        chunk.alignCameras()
    doc.save()


def wczytanie_punktow():
    punkty = Metashape.app.getOpenFileName('plik z punktami osnowy')
    for chunk in doc.chunks:
        chunk.importReference(path=punkty, format=Metashape.ReferenceFormatCSV, columns='nyxz',
                              delimiter='\t', create_markers=True)

        chunk.crs = Metashape.CoordinateSystem("EPSG::4326")
        chunk.marker_crs = Metashape.CoordinateSystem("EPSG::2178")
    doc.save()


def zapis_markerow():
    for chunk in doc.chunks:
        chunk.alignCameras()
        chunk.exportReference(path=output + '/' + chunk.label + '.txt', format=Metashape.ReferenceFormatCSV,
                              items=Metashape.ReferenceItemsCameras, columns='', delimiter='\t')
    doc.save()


def usuniecie_20ppunktow():
    TARGET_PERCENT = 80
    for chunk in doc.chunks:
        points = chunk.point_cloud.points
        f = Metashape.PointCloud.Filter()
        f.init(chunk, criterion=Metashape.PointCloud.Filter.ReprojectionError)  # Reprojection Error
        list_values = f.values
        list_values_valid = list()
        for i in range(len(list_values)):
            if points[i].valid:
                list_values_valid.append(list_values[i])
        list_values_valid.sort()
        target = int(len(list_values_valid) * TARGET_PERCENT / 100)
        threshold = list_values_valid[target]
        f.selectPoints(threshold)
        f.removePoints(threshold)
    doc.save()


def chmura_punktow():
    for chunk in doc.chunks:
        chunk.buildDepthMaps(downscale=16, filter_mode=Metashape.MildFiltering)  # lowest?
        chunk.buildDenseCloud()
    doc.save()


def siatka_aerotriangulacyjna():
    for chunk in doc.chunks:
        chunk.buildModel(source_data=Metashape.DenseCloudData)
    doc.save()


def NMPT_ortofotomapa():
    for chunk in doc.chunks:
        chunk.buildOrthomosaic(surface_data=Metashape.ModelData)
        chunk.buildDem(source_data=Metashape.DenseCloudData)
    doc.save()


def zapis_wynikow():
    doc.mergeChunks(merge_orthomosaics=True)
    for chunk in doc.chunks:
        if chunk.label == "Merged Chunk":
            chunk.exportRaster(path=output + '/ortofotomapa.tif', source_data=Metashape.OrthomosaicData)
    doc.save()


Metashape.app.removeMenuItem("Projekt1")

Metashape.app.addMenuItem("Projekt1/Automatyczne wczytanie zdjęć z folderów", wczytanie_zdjec)
Metashape.app.addMenuItem("Projekt1/Orientacja zdjęć", orientacja_zdjec)
Metashape.app.addMenuItem("Projekt1/Wczytanie punktów osnowy z pliku", wczytanie_punktow)
Metashape.app.addMenuItem("Projekt1/Zapis do pliku tekstowego położenia markerów wraz z błędami ‘reprojection error’",
                          zapis_markerow)
Metashape.app.addMenuItem(
    "Projekt1/Usunięcie 20% punktów ‘key points’ na podstawie kryterium błędu ‘reprojection error’",
    usuniecie_20ppunktow)
Metashape.app.addMenuItem("Projekt1/Wygenerowanie gęstej chmury punktów", chmura_punktow)
Metashape.app.addMenuItem("Projekt1/Wygenerowanie siatki aerotriangulacyjnej", siatka_aerotriangulacyjna)
Metashape.app.addMenuItem("Projekt1/Wygenerowanie NMPT oraz ortofotomapy", NMPT_ortofotomapa)
Metashape.app.addMenuItem("Projekt1/Zapis do pliku wyników po połączeniu chunków", zapis_wynikow)
