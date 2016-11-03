import win32ui
import win32print
import win32con

from PIL import Image, ImageWin

'''
def send_to_printer(title,txt):
    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(win32print.GetDefaultPrinter())
    hDC.StartDoc(title)
    hDC.StartPage()
    hDC.SetMapMode(win32con.MM_TWIPS)

    ulc_x = 1000
    ulc_y = -1000
    lrc_x = 11500
    lrc_y = -11500

    hDC.DrawText(txt,(ulc_x,ulc_y,lrc_x,lrc_y),win32con.DT_LEFT)

    hDC.EndPage()
    hDC.EndDoc()

send_to_printer("123","123")

'''

def send_to_printer(imagename):


	#
	# Constants for GetDeviceCaps
	#
	#
	# HORZRES / VERTRES = printable area
	#
	HORZRES = 8
	VERTRES = 10
	#
	# LOGPIXELS = dots per inch
	#
	LOGPIXELSX = 88
	LOGPIXELSY = 90
	#
	# PHYSICALWIDTH/HEIGHT = total area
	#
	PHYSICALWIDTH = 110
	PHYSICALHEIGHT = 111
	#
	# PHYSICALOFFSETX/Y = left / top margin
	#
	PHYSICALOFFSETX = 112
	PHYSICALOFFSETY = 113

	printer_name = win32print.GetDefaultPrinter ()
	# file_name = "test.jpg"
	file_name = imagename

	#
	# You can only write a Device-independent bitmap
	#  directly to a Windows device context; therefore
	#  we need (for ease) to use the Python Imaging
	#  Library to manipulate the image.
	#
	# Create a device context from a named printer
	#  and assess the printable size of the paper.
	#
	hDC = win32ui.CreateDC ()
	hDC.CreatePrinterDC (printer_name)
	printable_area = hDC.GetDeviceCaps (HORZRES), hDC.GetDeviceCaps (VERTRES)
	printer_size = hDC.GetDeviceCaps (PHYSICALWIDTH), hDC.GetDeviceCaps (PHYSICALHEIGHT)
	printer_margins = hDC.GetDeviceCaps (PHYSICALOFFSETX), hDC.GetDeviceCaps (PHYSICALOFFSETY)

	#
	# Open the image, rotate it if it's wider than
	#  it is high, and work out how much to multiply
	#  each pixel by to get it as big as possible on
	#  the page without distorting.
	#
	bmp = Image.open (file_name)
	if bmp.size[0] > bmp.size[1]:
		bmp = bmp.rotate (90)

	ratios = [1.0 * printable_area[0] / bmp.size[0], 1.0 * printable_area[1] / bmp.size[1]]
	scale = min (ratios)

	#
	# Start the print job, and draw the bitmap to
	#  the printer device at the scaled size.
	#
	hDC.StartDoc (file_name)
	hDC.StartPage ()

	dib = ImageWin.Dib (bmp)
	scaled_width, scaled_height = [int (scale * i) for i in bmp.size]
	x1 = int ((printer_size[0] - scaled_width) / 2)
	y1 = int ((printer_size[1] - scaled_height) / 2)
	x2 = x1 + scaled_width
	y2 = y1 + scaled_height
	dib.draw (hDC.GetHandleOutput (), (x1, y1, x2, y2))

	hDC.EndPage ()
	hDC.EndDoc ()
	hDC.DeleteDC ()