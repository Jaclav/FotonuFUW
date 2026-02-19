#!/bin/python3

import time
from ctypes import byref
import os
import sys
import datetime

from HH import *

# Measurement parameters, these are hardcoded since this is just a demo
binning = 0  # you can change this
offset = 0
tacq = 10000  # Measurement time in millisec, you can change this
syncDivider = 1  # you can change this
syncCFDZeroCross = 10  # you can change this (in mV)
syncCFDLevel = 50  # you can change this (in mV)
syncChannelOffset = -5000  # you can change this (in ps, like a cable delay)
inputCFDZeroCross = 10  # you can change this (in mV)
inputCFDLevel = 50  # you can change this (in mV)
inputChannelOffset = 0  # you can change this (in ps, like a cable delay)
cmd = 0

now = datetime.datetime.now()
outputfile = open("histomode_"+str(now)+".out", "w+")

outputfile.write("Binning           : %d\n" % binning)
outputfile.write("Offset            : %d\n" % offset)
outputfile.write("AcquisitionTime   : %d\n" % tacq)
outputfile.write("SyncDivider       : %d\n" % syncDivider)
outputfile.write("SyncCFDZeroCross  : %d\n" % syncCFDZeroCross)
outputfile.write("SyncCFDLevel      : %d\n" % syncCFDLevel)
outputfile.write("InputCFDZeroCross : %d\n" % inputCFDZeroCross)
outputfile.write("InputCFDLevel     : %d\n" % inputCFDLevel)

loadDevice()

# Histo mode with internal clock
tryfunc(
    hhlib.HH_Initialize(ct.c_int(dev[0]), ct.c_int(MODE_HIST), ct.c_int(0)),
    "Initialize",
)

getDeviceInfo()

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
print("Histogram length is %d" % histLen.value)

tryfunc(hhlib.HH_SetBinning(ct.c_int(dev[0]), ct.c_int(binning)), "SetBinning")
tryfunc(hhlib.HH_SetOffset(ct.c_int(dev[0]), ct.c_int(offset)), "SetOffset")
tryfunc(hhlib.HH_GetResolution(ct.c_int(dev[0]), byref(resolution)), "GetResolution")
print("Resolution is %1.1lfps" % resolution.value)
outputfile.write("Resolution        : %d\n" % resolution.value)


# Note: after Init or SetSyncDiv you must allow >400 ms for valid  count rate readings
# Otherwise you get new values after every 100ms
time.sleep(0.4)

tryfunc(hhlib.HH_GetSyncRate(ct.c_int(dev[0]), byref(syncRate)), "GetSyncRate")
print("\nSyncrate=%1d/s" % syncRate.value)

for i in range(0, numChannels.value):
    tryfunc(
        hhlib.HH_GetCountRate(ct.c_int(dev[0]), ct.c_int(i), byref(countRate)),
        "GetCountRate",
    )
    print("Countrate[%1d]=%1d/s" % (i, countRate.value))

# new from v1.2: after getting the count rates you can check for warnings
tryfunc(hhlib.HH_GetWarnings(ct.c_int(dev[0]), byref(warnings)), "GetWarnings")
if warnings.value != 0:
    hhlib.HH_GetWarningsText(ct.c_int(dev[0]), warningstext, warnings)
    print("\n\n%s" % warningstext.value.decode("utf-8"))

tryfunc(
    hhlib.HH_SetStopOverflow(ct.c_int(dev[0]), ct.c_int(0), ct.c_int(10000)),
    "SetStopOverflow",
)  # for example only

while cmd != "q":
    tryfunc(hhlib.HH_ClearHistMem(ct.c_int(dev[0])), "ClearHistMem")

    print("press RETURN to start measurement")
    input()

    tryfunc(hhlib.HH_GetSyncRate(ct.c_int(dev[0]), byref(syncRate)), "GetSyncRate")
    print("Syncrate=%1d/s" % syncRate.value)

    for i in range(0, numChannels.value):
        tryfunc(
            hhlib.HH_GetCountRate(ct.c_int(dev[0]), ct.c_int(i), byref(countRate)),
            "GetCountRate",
        )
        print("Countrate[%1d]=%1d/s" % (i, countRate.value))

    # here you could check for warnings again

    tryfunc(hhlib.HH_StartMeas(ct.c_int(dev[0]), ct.c_int(tacq)), "StartMeas")
    print("\nMeasuring for %1d milliseconds..." % tacq)

    ctcstatus = ct.c_int(0)
    while ctcstatus.value == 0:
        tryfunc(hhlib.HH_CTCStatus(ct.c_int(dev[0]), byref(ctcstatus)), "CTCStatus")

    tryfunc(hhlib.HH_StopMeas(ct.c_int(dev[0])), "StopMeas")

    for i in range(0, numChannels.value):
        tryfunc(
            hhlib.HH_GetHistogram(
                ct.c_int(dev[0]), byref(counts[i]), ct.c_int(i), ct.c_int(0)
            ),
            "GetHistogram",
        )

        integralCount = 0
        for j in range(0, histLen.value):
            integralCount += counts[i][j]

        print("  Integralcount[%1d]=%1.0lf" % (i, integralCount))

    tryfunc(hhlib.HH_GetFlags(ct.c_int(dev[0]), byref(flags)), "GetFlags")

    if flags.value & FLAG_OVERFLOW > 0:
        print("  Overflow.")

    print("Enter c to continue or q to quit and save the count data.")
    cmd = input()

# writing to file
for j in range(0, histLen.value):
    for i in range(0, numChannels.value):
        outputfile.write("%5d " % counts[i][j])
    outputfile.write("\n")

closeDevices()
outputfile.close()
