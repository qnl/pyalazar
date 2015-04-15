cdef extern from "AlazarCmd.h":
	#Cython API for AlazarCmd.h
	cdef int LED_OFF
	cdef int LED_ON

cdef extern from "AlazarError.h":
	#Cython API for definitions in AlazarError.h

	# we never raise these and we use the default handling library, so
	# we don't need to fill the enum variants.
	enum _RETURN_CODE:
		pass

	ctypedef _RETURN_CODE RETURN_CODE
	# Acquisition card return codes.


cdef extern from "AlazarApi.h":
	# Cython API for Alazar C API.

	# typedefs

	# Keep the Alazar conventions for integer type shorthand.
	ctypedef signed char S8
	ctypedef unsigned char U8
	ctypedef signed short S16
	ctypedef unsigned short U16
	ctypedef signed long S32
	ctypedef unsigned long U32

	ctypedef void* HANDLE
	# Raw pointer to an Alazar board.


	# --- troubleshooting functions

	RETURN_CODE AlazarReadWriteTest(HANDLE h,
									U32* Buffer,
									U32 SizeToWrite,
									U32 SizeToRead)
	RETURN_CODE AlazarMemoryTest(HANDLE h, U32* errors)
	RETURN_CODE AlazarBusyFlag(HANDLE h, int* BusyFlag)
	RETURN_CODE AlazarTriggeredFlag(HANDLE h, int* TriggeredFlag)
	U32 AlazarBoardsFound()
	HANDLE AlazarOpen(char* BoardNameID); # e.x. ATS850-0, ATS850-1 ....
	void AlazarClose(HANDLE h);
	U32 AlazarGetBoardKind(HANDLE h);
	RETURN_CODE AlazarGetCPLDVersion(HANDLE h, U8* Major, U8* Minor);
	RETURN_CODE AlazarGetChannelInfo(HANDLE h, U32* MemSize, U8* SampleSize);
	RETURN_CODE AlazarGetSDKVersion(U8* Major, U8* Minor, U8* Revision);
	RETURN_CODE AlazarGetDriverVersion(U8* Major, U8* Minor, U8* Revision);
	RETURN_CODE AlazarGetBoardRevision(HANDLE hBoard, U8* Major, U8* Minor);


	# --- Input control ---

	RETURN_CODE AlazarInputControl(HANDLE h,
								   U8 channel,
								   U32 coupling,
								   U32 input_range,
								   U32 impedance)

	RETURN_CODE AlazarInputControlEx(HANDLE h,
									 U32 Channel,
									 U32 Coupling,
									 U32 InputRange,
									 U32 Impedance)
	RETURN_CODE AlazarSetPosition(HANDLE h,
								  U8 Channel,
								  int PMPercent,
								  U32 InputRange)

	RETURN_CODE AlazarSetExternalTrigger(HANDLE h, U32 Coupling, U32 Range)


	# --- Trigger operations ---

	RETURN_CODE AlazarSetTriggerDelay(HANDLE h, U32 Delay)

	RETURN_CODE AlazarSetTriggerTimeOut(HANDLE h, U32 to_ns)

	U32 AlazarTriggerTimedOut(HANDLE h)

	RETURN_CODE AlazarSetTriggerOperation(HANDLE h,
                                      U32 TriggerOperation,
                                      U32 TriggerEngine1,
                                      U32 Source1,
                                      U32 Slope1,
                                      U32 Level1,
                                      U32 TriggerEngine2,
                                      U32 Source2,
                                      U32 Slope2,
                                      U32 Level2)


	# --- Capture functions ---
	RETURN_CODE AlazarAbortCapture(HANDLE h)
	RETURN_CODE AlazarForceTrigger(HANDLE h)
	RETURN_CODE AlazarForceTriggerEnable(HANDLE h)
	RETURN_CODE AlazarStartCapture(HANDLE h)
	RETURN_CODE AlazarCaptureMode(HANDLE h, U32 Mode)

	# --- Status functions ---
	U32 AlazarBusy(HANDLE h)
	U32 AlazarTriggered(HANDLE h)
	U32 AlazarGetStatus(HANDLE h)


	# --- MulRec functions ---
	U32 AlazarDetectMultipleRecord(HANDLE h)
	RETURN_CODE AlazarSetRecordCount(HANDLE h, U32 Count)
	RETURN_CODE AlazarSetRecordSize(HANDLE h, U32 PreSize, U32 PostSize)


	# --- Clock control ---

	RETURN_CODE AlazarSetCaptureClock(HANDLE h,
									  U32 source,
									  U32 rate,
									  U32 edge,
									  U32 decimation)

	RETURN_CODE AlazarSetExternalClockLevel(HANDLE h, float percent)

	RETURN_CODE AlazarSetClockSwitchOver(HANDLE hBoard,
                                     	 U32 uMode,
                                     	 U32 uDummyClockOnTime_ns,
                                     	 U32 uReserved)


	# --- data transfer functions ---
	U32 AlazarRead(HANDLE h,
	               U32 Channel,
	               void* Buffer,
	               int ElementSize,
	               long Record,
	               long TransferOffset,
	               U32 TransferLength)


	# --- handle and system management functions ---
	HANDLE AlazarGetSystemHandle(U32 sid)
	U32 AlazarNumOfSystems()
	U32 AlazarBoardsInSystemBySystemID(U32 sid)
	U32 AlazarBoardsInSystemByHandle(HANDLE systemHandle)
	HANDLE AlazarGetBoardBySystemID(U32 sid, U32 brdNum)
	HANDLE AlazarGetBoardBySystemHandle(HANDLE systemHandle, U32 brdNum)
	RETURN_CODE AlazarSetLED(HANDLE h, U32 state)


	# --- board capability query functions ---

	RETURN_CODE AlazarQueryCapability(HANDLE h,
									  U32 request,
									  U32 value,
									  U32* retValue)

	RETURN_CODE AlazarGetMaxRecordsCapable(HANDLE h, U32 RecordLength, U32* num)


	# --- assorted orphans? ---

	RETURN_CODE AlazarSetBWLimit(HANDLE h, U32 Channel, U32 enable)
	RETURN_CODE AlazarSleepDevice(HANDLE h, U32 state)


	# --- asynchronous acquisition ---

	RETURN_CODE AlazarBeforeAsyncRead(HANDLE hBoard,
                      				  U32 uChannelSelect,
                      				  long lTransferOffset,
                      				  U32 uSamplesPerRecord,
                      				  U32 uRecordsPerBuffer,
                      				  U32 uRecordsPerAcquisition,
                      				  U32 uFlags)

	RETURN_CODE AlazarAbortAsyncRead(HANDLE hBoard)

	RETURN_CODE AlazarPostAsyncBuffer(HANDLE hDevice,
									  void* pBuffer,
									  U32 uBufferLength_bytes)

	RETURN_CODE AlazarWaitAsyncBufferComplete(HANDLE hDevice,
											  void* pBuffer,
											  U32 uTimeout_ms)

	RETURN_CODE AlazarWaitNextAsyncBufferComplete(HANDLE hDevice,
                                  				  void* pBuffer,
                                  				  U32 uBufferLength_bytes,
                                				  U32 uTimeout_ms)

	# --- DAC control ---

	RETURN_CODE AlazarConfigureAuxIO(HANDLE hDevice,
									 U32 uMode,
									 U32 uParameter)


	# --- process return code to text ---
	const char* AlazarErrorToText(RETURN_CODE code)

	# --- get board revision ---
	RETURN_CODE AlazarGetBoardRevision(HANDLE hBoard, U8* Major, U8* Minor)