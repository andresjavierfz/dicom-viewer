import pydicom
ds = pydicom.dcmread("samples/image-000002.dcm")
print(ds)