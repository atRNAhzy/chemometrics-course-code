resultCreate,id = ModbusCreate('192.168.192.5', 502, 1)			---创建Modbus主站
if resultCreate == 0 then
	print("Create modbus master success!")
else
    print("Create modbus master failed, code:", resultCreate)
end
Sync()

POS = {P7}
SpeedFactor(5)

 --称量抓取子程序
function CCD_run5() 
	SpeedFactor(10)
Move(P1,"SpeedS=50 SYNC=1 ")
Sleep(1000)

local Coils = {1}
SetCoils(id,9,#Coils,Coils)						--获得AGV控制权
Sleep(1000)
SetHoldRegs(id,0,1,{1},"U16")
--发送AGV去1号工位的信号
repeat
Sleep(1000)
until(GetInRegs(id,8,1,"U16")[1])== 4

	SetHoldRegs(id,0,1,{2},"U16")
	Sleep(10000)
	Move(P1,"SpeedS=50 SYNC=1 ")
	Sleep(3000)	
	Move(P2,"SpeedS=50 SYNC=1 ")
	Sleep(3000)	
	Move(P3,"SpeedS=50 SYNC=1 ")
	Sleep(10000)

	Move(P2,"SpeedS=50 SYNC=1 ")
	Sleep(3000)	
	Move(P1,"SpeedS=50 SYNC=1 ")
	Sleep(10000)
	
	SetHoldRegs(id,0,1,{3},"U16")
	Sleep(3000)	
	Move(P4,"SpeedS=50 SYNC=1 ")
	Sleep(3000)	
	Move(P5,"SpeedS=50 SYNC=1 ")
	Sleep(10000)
	Move(P1,"SpeedS=50 SYNC=1 ")
	Sleep(10000)
	
	SetHoldRegs(id,0,1,{1},"U16")
	Sleep(10000)
end