# Jaclav's wrapper for HydraHarp 400, makes life easier

# Info of original demo from https://github.com/PicoQuant/HH400-v3.x-Demos
# Demo for access to HydraHarp 400 Hardware via HHLIB.DLL v 3.0.
# Authors of the original demo:
# Keno Goertz, PicoQuant GmbH, February 2018

# From hhdefin.h
LIB_VERSION = "3.0"
MAXDEVNUM = 8
MODE_HIST = 0
MAXLENCODE = 6
HHMAXINPCHAN = 8
MAXHISTLEN = 65536
FLAG_OVERFLOW = 0x001

import ctypes as ct
from ctypes import byref
import time

# Variables to store information read from DLLs
counts = [(ct.c_uint * MAXHISTLEN)() for i in range(0, HHMAXINPCHAN)]
dev = []
libVersion = ct.create_string_buffer(b"", 8)
hwSerial = ct.create_string_buffer(b"", 8)
hwPartno = ct.create_string_buffer(b"", 8)
hwVersion = ct.create_string_buffer(b"", 8)
hwModel = ct.create_string_buffer(b"", 16)
errorString = ct.create_string_buffer(b"", 40)
numChannels = ct.c_int()
histLen = ct.c_int()
resolution = ct.c_double()
syncRate = ct.c_int()
countRate = ct.c_int()
flags = ct.c_int()
warnings = ct.c_int()
warningstext = ct.create_string_buffer(b"", 16384)

hhlib = ct.CDLL("/usr/local/lib64/hh400/hhlib.so")


def closeDevices():
    for i in range(0, MAXDEVNUM):
        hhlib.HH_CloseDevice(ct.c_int(i))


def tryfunc(retcode, funcName, measRunning=False):
    if retcode < 0:
        hhlib.HH_GetErrorString(errorString, ct.c_int(retcode))
        print(
            "HH_%s error %d (%s). Aborted."
            % (funcName, retcode, errorString.value.decode("utf-8"))
        )
        closeDevices()


def loadHHLibrary():
    hhlib.HH_GetLibraryVersion(libVersion)
    print("HH library version is %s" % libVersion.value.decode("utf-8"))
    if libVersion.value.decode("utf-8") != LIB_VERSION:
        print("Warning: The application was built for version %s" % LIB_VERSION)


def findAndConnect():
    print("\nSearching for HydraHarp devices...")
    print("Dev_idx     Status")

    for i in range(0, MAXDEVNUM):
        retcode = hhlib.HH_OpenDevice(ct.c_int(i), hwSerial)
        if retcode == 0:
            print("  %1d        S/N %s" % (i, hwSerial.value.decode("utf-8")))
            dev.append(i)
        else:
            if retcode == -1:  # HH_ERROR_DEVICE_OPEN_FAIL
                print("  %1d        no device" % i)
            else:
                hhlib.HH_GetErrorString(errorString, ct.c_int(retcode))
                print("  %1d        %s" % (i, errorString.value.decode("utf8")))

    # In this demo we will use the first HydraHarp device we find, i.e. dev[0].
    # You can also use multiple devices in parallel.
    # You can also check for specific serial numbers, so that you always know
    # which physical device you are talking to.

    if len(dev) < 1:
        print("No device available.")
        closeDevices()
    print("Using device #%1d" % dev[0])
    print("\nInitializing the device...")

    # Histo mode with internal clock
    tryfunc(
        hhlib.HH_Initialize(ct.c_int(dev[0]), ct.c_int(MODE_HIST), ct.c_int(0)),
        "Initialize",
    )


def getInfo():
    # Only for information
    tryfunc(
        hhlib.HH_GetHardwareInfo(dev[0], hwModel, hwPartno, hwVersion),
        "GetHardwareInfo",
    )
    out = (
        "Found Model "
        + hwModel.value.decode("utf-8")
        + " Part no "
        + hwPartno.value.decode("utf-8")
        + " Version "
        + hwVersion.value.decode("utf-8")
    )

    tryfunc(
        hhlib.HH_GetNumOfInputChannels(ct.c_int(dev[0]), byref(numChannels)),
        "GetNumOfInputChannels",
    )
    out += "\nDevice has " + str(numChannels.value) + " input channels."
    return out


def getSyncCountRates():
    # Note: after Init or SetSyncDiv you must allow >400 ms for valid  count rate readings
    # Otherwise you get new values after every 100ms
    time.sleep(0.4)

    tryfunc(hhlib.HH_GetSyncRate(ct.c_int(dev[0]), byref(syncRate)), "GetSyncRate")
    print("Syncrate=%1d/s" % syncRate.value)
    for i in range(0, numChannels.value):
        tryfunc(
            hhlib.HH_GetCountRate(ct.c_int(dev[0]), ct.c_int(i), byref(countRate)),
            "GetCountRate",
        )
        print("Countrate[%1d]=%1d/s" % (i, countRate.value))


def getWarnings():
    # new from v1.2: after getting the count rates you can check for warnings
    tryfunc(hhlib.HH_GetWarnings(ct.c_int(dev[0]), byref(warnings)), "GetWarnings")
    if warnings.value != 0:
        hhlib.HH_GetWarningsText(ct.c_int(dev[0]), warningstext, warnings)
        return warningstext.value.decode("utf-8")


def setEverything(
    binning=0,
    offset=0,
    syncDivider=1,
    syncCFDZeroCross=10,
    syncCFDLevel=600,
    syncChannelOffset=-5000,
    inputCFDZeroCross=10,
    inputCFDLevel=600,
    inputChannelOffset=0,
):
    """
    Sets all necessary data to run measurement,
    CFD stands for Constant Fraction Discriminator

    Args:
        binning (int, optional): measurement binning code minimum = 0 (smallest, i.e. base resolution). Defaults to 0.
        offset (int, optional): global time offset [ps]. Defaults to 0.
        syncDivider (int, optional): _description_. Defaults to 1.
        syncCFDZeroCross (int, optional): sync input Constant Fraction Discriminato 0 mV line offset [mV]. Defaults to 10.
        syncCFDLevel (int, optional): [mV]. Defaults to 50.
        syncChannelOffset (int, optional): [ps]. Defaults to -5000.
        inputCFDZeroCross (int, optional): [mV]. Defaults to 10.
        inputCFDLevel (int, optional): [mV]. Defaults to 50.
        inputChannelOffset (int, optional): [ps]. Defaults to 0.

    Returns:
        str: output message
    """

    out = ""
    print("\nCalibrating...")
    tryfunc(hhlib.HH_Calibrate(ct.c_int(dev[0])), "Calibrate")
    tryfunc(hhlib.HH_SetSyncDiv(ct.c_int(dev[0]), ct.c_int(syncDivider)), "SetSyncDiv")

    tryfunc(
        hhlib.HH_SetSyncCFD(
            ct.c_int(dev[0]), ct.c_int(syncCFDLevel), ct.c_int(syncCFDZeroCross)
        ),
        "SetSyncCFD",
    )

    tryfunc(
        hhlib.HH_SetSyncChannelOffset(ct.c_int(dev[0]), ct.c_int(syncChannelOffset)),
        "SetSyncChannelOffset",
    )

    # we use the same input settings for all channels, you can change this
    for i in range(0, numChannels.value):
        tryfunc(
            hhlib.HH_SetInputCFD(
                ct.c_int(dev[0]),
                ct.c_int(i),
                ct.c_int(inputCFDLevel),
                ct.c_int(inputCFDZeroCross),
            ),
            "SetInputCFD",
        )

        tryfunc(
            hhlib.HH_SetInputChannelOffset(
                ct.c_int(dev[0]), ct.c_int(i), ct.c_int(inputChannelOffset)
            ),
            "SetInputChannelOffset",
        )

    tryfunc(
        hhlib.HH_SetHistoLen(ct.c_int(dev[0]), ct.c_int(MAXLENCODE), byref(histLen)),
        "SetHistoLen",
    )
    out += "Histogram length  : " + str(histLen.value) + "\n"

    tryfunc(hhlib.HH_SetBinning(ct.c_int(dev[0]), ct.c_int(binning)), "SetBinning")
    tryfunc(hhlib.HH_SetOffset(ct.c_int(dev[0]), ct.c_int(offset)), "SetOffset")

    out += "Binning           : " + str(binning) + "\n"
    out += "Offset            : " + str(offset) + "\n"
    out += "SyncDivider       : " + str(syncDivider) + "\n"
    out += "SyncCFDZeroCross  : " + str(syncCFDZeroCross) + "\n"
    out += "SyncCFDLevel      : " + str(syncCFDLevel) + "\n"
    out += "InputCFDZeroCross : " + str(inputCFDZeroCross) + "\n"
    out += "InputCFDLevel     : " + str(inputCFDLevel) + "\n"

    tryfunc(
        hhlib.HH_GetResolution(ct.c_int(dev[0]), byref(resolution)), "GetResolution"
    )
    out += "Resolution        : %1.1lf ps" % resolution.value + "\n"
    return out


def measureAllInputs(tacq):
    """Measurement in histogram mode

    Args:
        tacq (int): acquisition time [ms]

    Returns:
        data (tuple): outputMessage, length of histogram, number of channels and 2d array of counts
    """

    out = "AcquisitionTime   : " + str(tacq) + "\n"
    tryfunc(hhlib.HH_ClearHistMem(ct.c_int(dev[0])), "ClearHistMem")

    # measurement
    tryfunc(hhlib.HH_StartMeas(ct.c_int(dev[0]), ct.c_int(tacq)), "StartMeas")
    out += "Measuring for " + str(tacq) + " milliseconds...\n"
    ctcstatus = ct.c_int(0)
    while ctcstatus.value == 0:
        tryfunc(hhlib.HH_CTCStatus(ct.c_int(dev[0]), byref(ctcstatus)), "CTCStatus")
    tryfunc(hhlib.HH_StopMeas(ct.c_int(dev[0])), "StopMeas")

    for i in range(0, numChannels.value):
        tryfunc(
            hhlib.HH_GetHistogram(
                ct.c_int(dev[0]), byref(counts[i]), ct.c_int(i), ct.c_int(1)
            ),
            "GetHistogram",
        )
        integralCount = 0
        for j in range(0, histLen.value):
            integralCount += counts[i][j]
        out += "  Integralcount[" + str(i) + "]=" + str(integralCount) + "\n"
    tryfunc(hhlib.HH_GetFlags(ct.c_int(dev[0]), byref(flags)), "GetFlags")
    if flags.value & FLAG_OVERFLOW > 0:
        out += "ERROR:  Overflow."

    return (out, histLen.value, numChannels.value, counts)
