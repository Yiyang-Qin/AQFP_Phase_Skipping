import random
import matplotlib.pyplot as plt
#Graph Node Class Definitions
class Node:
    def __init__(self,name,gate_type,inputs,inversions):
        self.name = name
        self.gate_type = gate_type
        self.inputs = inputs
        self.inversions=inversions
        self.fanouts = []
        self.ASAP = 0
        self.freeze_ASAP=0
        self.ALAP = 0
        self.slack = 0
        self.depth = 0
        self.depth_id = 0
        self.splitter_in = []
        self.splitter_out =[]
        self.Find_ASAP()
        self.phases = 4
        for i in inputs:
            self.splitter_in.append(0)
        self.updateFanouts()
    def __str__(self):
        clk = self.depth%self.phases
        if (clk==0):
            clk=self.phases
        line = self.gate_type+"_AQFP "+self.name+"_"+"( clk_"+str(clk)+" , "
        for i in self.inputs:
            line += i.name + " , "
        for inv in self.inversions:
            line += str(inv)+ " , "
        line+=self.name+" );\n"
        return line
    def Find_Slack(self,phases):
        if (self.gate_type =="maj3" or self.gate_type =="PO" or self.gate_type=="PI"):
            self.slack=0
        elif (len(self.fanouts)==1):
            self.slack = self.fanouts[0].depth - self.depth - phases
        elif (len(self.splitter_out)==1):
            self.slack = self.splitter_out[0].depth - self.depth -phases
    def Find_ASAP(self):
        if (len(self.inputs)==0):
            self.ASAP=1
        else:
            temp=1
            for i in self.inputs:
                if i.ASAP < 1:
                    i.ASAP = 1
                temp = max(temp, i.ASAP + 1)
            self.ASAP=temp
        for fanout in self.fanouts:
            if fanout.ASAP + 1 <= self.ASAP:
                fanout.Find_ASAP()
    def Find_ALAP(self, Loutputs):
        if self.gate_type == "PO":
            self.ALAP = Loutputs
        elif (len(self.fanouts)==0 or len(self.inputs)==0):
            self.ALAP=self.ASAP
        else:
            temp = 999999
            for o in self.fanouts:
                if (o.ALAP > 0):
                    temp = min(temp, o.ALAP - 1)
            self.ALAP = temp
        for i in self.inputs:
            if i.ALAP == 0 or i.ALAP > self.ALAP + 1:
                i.Find_ALAP(Loutputs)
    def addFanout(self,fanout):
        self.fanouts.append(fanout)
    def connect_splitter(self,fanouts,root):
        for f in fanouts:
            f.add_splitter(root,self)
            self.addFanout(f)
    def updateFanouts(self):
        if (self.gate_type=="splitter"):
            self.inputs[0].splitter_out.append(self)
            if(self.inputs[0].gate_type == "splitter"):
                self.splitter_in = self.inputs
                self.inputs[0].fanouts.append(self)
        else:
            for i in self.inputs:
                i.addFanout(self)
    def reset_splitters(self):
        self.splitter_out =[]
        for f in self.fanouts:
            index = 0
            count = -1
            for i in f.inputs:
                count+=1
                if (i.name == self.name):
                    index = count
            f.splitter_in[index] = 0
    def add_splitter(self,root,splitter):
        index = 0
        count = -1
        for i in self.inputs:
            count+=1
            if (i.name == root.name):
                index = count
        self.splitter_in[index] = splitter
    def insertbuf(self,driver,buf):
        index = -1
        for s in self.inputs:
            index+=1
            if (s.name==driver.name):
                self.inputs[index]=buf
    def clean_connections(self):
        index =-1
        for i in self.inputs:
            index+=1
            if (self.splitter_in[index]==0):
                continue
            else:
                self.inputs[index]=self.splitter_in[index]
        #remove all inputs that are indirect, replace them with a splitter input if one exists
            

class Ntk:
    def __init__(self,name):
        self.name = name
        self.dict = {}
        self.netlist = []
        self.splitters = []
        self.s_dict = {}
        self.phases=8
        self.POs = []
        self.PIs = []
        self.wires = []
        self.maxDepth = 0
    def set_phases(self):
        for n in self.netlist:
            n.phases = self.phases
        for s in self.splitters:
            s.phases = self.phases
    def add(self,node):
        self.netlist.append(node)
        self.dict[node.name]=len(self.netlist)-1
        if (node.gate_type != "PO" and node.gate_type != "PI"):
            self.wires.append(node.name)
    def add_splitter(self,splitter):
        self.splitters.append(splitter)
        self.s_dict[splitter.name]=len(self.splitters)-1
    def Obj(self,ID):
        return self.netlist[self.dict[ID]]
    def Set_ALAP(self):
        for n in reversed(self.netlist):
            n.Find_ALAP()
    def Fix_outputs(self):
        depth = 0
        for n in self.netlist:
            if (n.gate_type=="PO"):
                if (depth<n.ASAP):
                    depth = n.ASAP
        for n in self.netlist:
            if (n.gate_type=="PO"):
                n.ASAP = depth
                n.ALAP = depth
    def parse(self,filename):
        file = open(filename,'r')
        lines = file.readlines()
        for line in lines:
            entry = line.split()
            if (entry[0]=="module"):
                self.name = entry[1].split("(")[0]
            elif (entry[0]=="input"):
                for PI in entry:
                    if (PI!="input" and PI!="," and PI!=";"):
                        temp = Node(PI,"PI",[],[])
                        self.add(temp)
                        self.PIs.append(PI)
            elif (entry[0]=="assign"):
                node_name = entry[1]
                if (entry[3]=="("):
                    temp = entry[4].split("~")
                    in1 = temp[-1]
                    inv1 = len(temp)-1
                    temp = entry[6].split("~")
                    in2 = temp[-1]
                    inv2 = len(temp)-1
                    temp = entry[12].split("~")
                    in3 = temp[-1]
                    inv3 = len(temp)-1
                    new = Node(node_name,"maj3",[self.Obj(in1),self.Obj(in2),self.Obj(in3)],[inv1,inv2,inv3])
                    self.add(new)
                    new.splitter_in = [0,0,0]
                elif(entry[4]=="&"):
                    temp = entry[3].split("~")
                    in1 = temp[-1]
                    inv1 = len(temp)-1
                    temp = entry[5].split("~")
                    in2 = temp[-1]
                    inv2 = len(temp)-1
                    new = Node(node_name,"and",[self.Obj(in1),self.Obj(in2)],[inv1,inv2])
                    self.add(new)
                    new.splitter_in = [0,0]
                elif(entry[4]=="|"):
                    temp = entry[3].split("~")
                    in1 = temp[-1]
                    inv1 = len(temp)-1
                    temp = entry[5].split("~")
                    in2 = temp[-1]
                    inv2 = len(temp)-1
                    new = Node(node_name,"or",[self.Obj(in1),self.Obj(in2)],[inv1,inv2])
                    self.add(new)
                    new.splitter_in = [0,0]
                else:
                    PO = entry[1]
                    temp = entry[3].split("~")
                    in1 = temp[-1]
                    inv1 = len(temp)-1
                    new = Node(PO,"PO",[self.Obj(in1)],[inv1])
                    self.add(new)
                    new.splitter_in = [0]
                    self.POs.append(PO)
        file.close()
    def deleteSplitters(self):
        for s in self.splitters:
            del s
        self.s_dict = {}
        self.splitters=[]
        for n in self.netlist:
            n.reset_splitters()
    def deleteTree(self,splitter_root):
        for s in splitter_root.splitter_out:
            self.deleteTree(s)
        self.splitters.pop(self.s_dict[splitter_root.name])
        del self.s_dict[splitter_root.name]
        del splitter_root
        #remove from list
        #remove from dict
        #del object
    def Print_depths(self):
        for n in self.netlist:
            print(n.name + " : " +str(n.depth))
        for s in self.splitters:
            print(s.name + ": " + str(s.depth))

    def Find_maxDepth(self):
        max_depth = 0
        for n in self.netlist:
            if n.gate_type == "PI":
                n.depth = 1
                n.Find_ASAP()
        for n in self.netlist:
            if n.gate_type != "PI":
                n.Find_ASAP()
        for n in self.splitters:
            n.Find_ASAP()
        for n in self.netlist:
           if n.gate_type != "PI":
               if len(n.fanouts) == 1:
                   n.depth = max(n.depth, n.fanouts[0].depth + 1)
               elif len(n.splitter_out) == 1:
                   n.depth = max(n.depth, n.splitter_out[0].depth + 1)
               else:
                   for fout in n.fanouts:
                       n.depth = max(n.depth, fout.depth + 1)
                   for sout in n.splitter_out:
                       n.depth = max(n.depth, sout.depth + 1)
               max_depth = max(max_depth, n.depth)
        for s in self.splitters:
           for g in s.fanouts:
               if (g.gate_type != "splitter"):
                   s.depth = max(s.depth, g.depth + 1)
           for sp in s.splitter_out:
               s.depth = max(s.depth, sp.depth + 1)
           max_depth = max(max_depth, s.depth)
        self.maxDepth = max_depth

    # def Find_ALAPASAP(self, Loutputs):
    #     for n in self.netlist:
    #         n.Find_ASAP()
    #         n.Find_ALAP(Loutputs)
    #     ASAP = {n.name: n.ASAP for n in self.netlist}
    #     ALAP = {n.name: n.ALAP for n in self.netlist}
    #     k_max = {}
    #     for n in self.netlist:
    #         for fanout in n.fanouts:
    #             k_max[(n.name, fanout.name)] = ALAP[fanout.name] - ASAP[n.name]
    #
    #     return ASAP, ALAP, k_max

    def Find_ALAPASAP(self, Loutputs):
        for n in self.netlist + self.splitters:
            n.Find_ASAP()
            n.Find_ALAP(Loutputs)
        ASAP = {n.name: n.ASAP for n in self.netlist + self.splitters}
        ALAP = {n.name: n.ALAP for n in self.netlist + self.splitters}
        k_max = {}
        for n in self.netlist:
            if len(n.splitter_out) == 1:
                fanout = n.splitter_out[0]
            elif len(n.fanouts) == 0:
                continue
            else:
                fanout = n.fanouts[0]
            k_max[(n.name, fanout.name)] = ALAP[fanout.name] - ASAP[n.name]

        for n in self.splitters:
            for fanout in n.fanouts + n.splitter_out:
                if fanout in n.fanouts and fanout.gate_type == "splitter":
                    continue
                k_max[(n.name, fanout.name)] = ALAP[fanout.name] - ASAP[n.name]

        return ASAP, ALAP, k_max

    def Print_info(self):
    
        total_cells = len(self.netlist) + len(self.splitters)
        # self.Find_maxDepth()
        self.maxDepth = 0
        for gate in self.netlist:
            if gate.depth > self.maxDepth:
                self.maxDepth = gate.depth

        max_depth = self.maxDepth
        widthAtDepth = {}
        cellsAtDepth = {}
        gateAtDepth = {}
        splitterAtDepth = {}
        bufferAtDepth = {}
        numOfInputs = 0

        for gate in self.netlist:
            gate_depth = gate.depth
            gate_width = len(gate.fanouts)
            if gate_depth not in widthAtDepth:
                widthAtDepth[gate_depth] = 0
                cellsAtDepth[gate_depth] = 0
                gateAtDepth[gate_depth] = 0
                splitterAtDepth[gate_depth] = 0
                bufferAtDepth[gate_depth] = 0
            widthAtDepth[gate_depth] = max(widthAtDepth[gate_depth], gate_width)
            # cellsAtDepth[gate_depth] += 1
            if gate_depth not in gateAtDepth:
                gateAtDepth[gate_depth] = 0
            if gate.gate_type == "buf":
                bufferAtDepth[gate_depth] += 1
                cellsAtDepth[gate_depth] += 1/3
            else:
                gateAtDepth[gate_depth] += 1
                cellsAtDepth[gate_depth] += 1
            if gate.gate_type == "PI":
                numOfInputs = numOfInputs + 1
                    
        for splitter in self.splitters:
            splitter_depth = splitter.depth
            splitter_width = len(splitter.fanouts)
            if splitter_depth not in widthAtDepth:
                widthAtDepth[splitter_depth] = 0
                cellsAtDepth[splitter_depth] = 0
                gateAtDepth[gate_depth] = 0
                splitterAtDepth[gate_depth] = 0
                bufferAtDepth[gate_depth] = 0
            if splitter_depth not in splitterAtDepth:
                splitterAtDepth[splitter_depth] = 0
            widthAtDepth[splitter_depth] = max(widthAtDepth[splitter_depth], splitter_width)
            # cellsAtDepth[splitter_depth] += 1
            cellsAtDepth[splitter_depth] += 1/3
            splitterAtDepth[splitter_depth] += 1
        
        if widthAtDepth:
            # max_width = max(cellsAtDepth.values())
            max_width = max(v for k, v in cellsAtDepth.items() if k != 1)
            # print(cellsAtDepth)
            print({k: round(v, 2) for k, v in cellsAtDepth.items()})
            avgWidthPerDepth = sum(cellsAtDepth.values()) / len(cellsAtDepth)
        else:
            max_width = 0
            avgWidthPerDepth = 0

        # Read the Width value from problem solution file
        width_from_solution = None
        try:
            with open('problem_sol.txt', 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3 and parts[1] == "Width":
                        width_from_solution = float(parts[2])
                        break
        except FileNotFoundError:
            print("Warning: problem_sol.txt not found.")
        print(f"Width from Solution: {width_from_solution:.2f}")

        print(f"Total Cells: {total_cells}")
        print(f"Max Depth: {max_depth}")
        print(f"Max Width: {max_width:.2f}")
        print(f"Average Width per Depth: {avgWidthPerDepth:.2f}")
        print(f"Number of Primary Inputs: {numOfInputs}")
    
        plt.figure(figsize=(12, 6))
        plt.subplot(2, 2, 1)
        # plt.bar(cellsAtDepth.keys(), cellsAtDepth.values())
        plt.bar(
            [k for k in cellsAtDepth.keys() if k != 1],
            [v for k, v in cellsAtDepth.items() if k != 1]
        )
        plt.xlabel('Depth')
        plt.ylabel('Max Fanout Width at Depth')
        plt.title('Overall Fanout Width by Depth')

        plt.subplot(2, 2, 2)
        # plt.bar(gateAtDepth.keys(), gateAtDepth.values())
        plt.bar(
            [k for k in gateAtDepth.keys() if k != 1],
            [v for k, v in gateAtDepth.items() if k != 1]
        )
        plt.xlabel('Depth')
        plt.ylabel('Max Gate Fanout Width')
        plt.title('Gate Fanout Width by Depth')
        
        plt.subplot(2, 2, 3)
        # plt.bar(splitterAtDepth.keys(), splitterAtDepth.values())
        plt.bar(
            [k for k in splitterAtDepth.keys() if k != 1],
            [v for k, v in splitterAtDepth.items() if k != 1]
        )
        plt.xlabel('Depth')
        plt.ylabel('Max Splitter Fanout Width')
        plt.title('Splitter Fanout Width by Depth')

        plt.subplot(2, 2, 4)
        if bufferAtDepth:
            # plt.bar(bufferAtDepth.keys(), bufferAtDepth.values())
            plt.bar(
                [k for k in bufferAtDepth.keys() if k != 1],
                [v for k, v in bufferAtDepth.items() if k != 1]
            )
            plt.xlabel('Depth')
            plt.ylabel('Max Buffer Fanout Width')
            plt.title('Buffer Fanout Width by Depth')
        else:
            plt.bar([], [])
            plt.title('No Buffers')

        plt.tight_layout()
        plt.show()

        # plt.savefig(f'Results/4_1_4/Gates_3_times_larger/Width_Optimized/{self.name}.png')  # Save the figure
        # plt.close()

    def CleanNtk(self):
        for g in self.netlist:
            g.clean_connections()
        for s in self.splitters:
            s.clean_connections()
    def verify(self,pr):
        buf = 0
        splits=0
        for n in self.netlist:
            if (n.gate_type=="buf"):
                buf+=1
            for i in n.inputs:
                if (n.depth>i.depth+pr):
                    print("ERROR:Netlist Check Failed on connection ("+i.name+","+str(i.depth)+") -> ("+n.name+","+str(n.depth)+")")
                    return False
        for s in self.splitters:
            splits+=1
            for i in n.inputs:
                if (n.depth>i.depth+pr):
                    print("ERROR:Netlist Check Failed on connection ("+i.name+","+str(i.depth)+") -> ("+n.name+","+str(n.depth)+")")
                    return False
        print("Network is Appropriately Balanced\nRecovered Inserted Cost:"+str(buf+splits)+"\nBuffers = "+str(buf)+"\nSplitters = "+str(splits))
        return True
        
import os
import math
import numpy

def Write_Equations_20_to_26(ntk, N, Loutputs, n, fanout, temp, ASAP, ALAP, k_max):
    edge = (n.name, fanout.name)
    max_k = k_max[edge]
    temp.write(f"C_{n.name}_{fanout.name} >= 0\n")

    # Equation (20)
    for k in range(1, max_k + 1):
        temp.write(f"C_{n.name}_{fanout.name}_{k} >= 0\n")
        if k > 1:
            temp.write(f"C_{n.name}_{fanout.name}_{k - 1} - C_{n.name}_{fanout.name}_{k} >= 0\n")
        if k < max_k:
            temp.write(f"C_{n.name}_{fanout.name}_{k} - C_{n.name}_{fanout.name}_{k + 1} >= 0\n")

    # Equation (21)
    sum_Cijk = " + ".join([f"C_{n.name}_{fanout.name}_{k}" for k in range(1, max_k + 1)])
    temp.write(f"{sum_Cijk} - C_{n.name}_{fanout.name} = 0\n")

    # Equation (22)
    for k in range(1, max_k + 1):
        sum_XijkL = " + ".join(
            [f"X_{n.name}_{fanout.name}_{k}_{L}" for L in range(1, ALAP[fanout.name] + 1)])
        temp.write(f"{sum_XijkL} - C_{n.name}_{fanout.name}_{k} = 0\n")

    # Equation (23)
    for k in range(1, max_k + 1):
        row_assignment = " + ".join(
            [f"{L} X_{n.name}_{fanout.name}_{k}_{L}" for L in range(1, ALAP[fanout.name] + 1)])
        temp.write(f"{row_assignment} - D_{n.name}_{fanout.name}_{k} = 0\n")
        # temp.write(f"{row_assignment} - C_{n.name}_{fanout.name}_{k}  {ALAP[fanout.name]} = 0\n")

    # Equation (24)
    for k in range(1, max_k + 1):
        # temp.write(f"L_{n.name}_{fanout.name}_{k} - L_{n.name} - (Loutputs - C_{n.name}_{fanout.name}_{k}) + Loutputs >= 0\n")
        if k == 1:
            temp.write(
                f"D_{n.name}_{fanout.name}_{k} - D_{n.name} -{Loutputs} C_{n.name}_{fanout.name}_{k} >= -{Loutputs - 1}\n")
            temp.write(
                f"D_{n.name} + {N} C_{n.name}_{fanout.name}_{k} - D_{n.name}_{fanout.name}_{k} >= 0\n")
        else:
            temp.write(
                f"D_{n.name}_{fanout.name}_{k} - D_{n.name}_{fanout.name}_{k - 1} -{Loutputs} C_{n.name}_{fanout.name}_{k} >= -{Loutputs - 1}\n")
            temp.write(
                f"D_{n.name}_{fanout.name}_{k - 1} + {N} C_{n.name}_{fanout.name}_{k} - D_{n.name}_{fanout.name}_{k} >= 0\n")
        # temp.write(f"L_{n.name} + P  C_{n.name}_{fanout.name}_{k} - L_{n.name}_{fanout.name}_{k} >= 0\n")

    # Equation (25) and (26)
    for k in range(1, max_k + 1):
        if k == max_k:
            temp.write(
                f"D_{fanout.name} + {Loutputs} C_{n.name}_{fanout.name}_{k} - D_{n.name}_{fanout.name}_{k} <= {N + Loutputs}\n")
        else:
            temp.write(
                f"D_{fanout.name} + {Loutputs} C_{n.name}_{fanout.name}_{k} - D_{n.name}_{fanout.name}_{k} - {Loutputs} C_{n.name}_{fanout.name}_{k + 1} <= {N + Loutputs}\n")

        temp.write(f" D_{n.name}_{fanout.name}_{k} >= 0\n")
        temp.write(f" D_{fanout.name} - D_{n.name}_{fanout.name}_{k} >= 1\n")

def Formulate_CPLEX(ntk,N, Loutputs, version):
    if version:
        obj_function=[]
        ASAP, ALAP, k_max = ntk.Find_ALAPASAP(Loutputs)
        with open('temp.txt', 'w') as temp:
            temp.write("Subject To\n")
            for n in ntk.netlist:
                # Gate level restriction for PI and PO: Equation (3) and (4)
                if (n.gate_type =="PI"):
                    # temp.write("D_"+n.name+" >= 1\n")
                    # temp.write("D_"+n.name+" <= 3\n")
                    temp.write("D_"+n.name+" = 1\n")
                if (n.gate_type=="PO"):
                    # temp.write("D_"+n.name+"-D_outputs = 0\n")
                    temp.write(f"D_outputs <= {Loutputs}\n")

                # Equation (2) for netlist gates
                else:
                    if (len(n.splitter_out)==1):
                        objfun="C_"+n.name+"_"+n.splitter_out[0].name
                        obj_function.append(objfun)
                        line = objfun + ">=0\n"
                        temp.write(line)
                        line = "D_"+n.splitter_out[0].name+" - D_"+n.name+">=1\n" 
                        temp.write(line)
                        line = "D_"+n.splitter_out[0].name+" - D_"+n.name+ "- "+str(N)+" "+objfun+" <= "+ str(N)+"\n"
                        temp.write(line)

                    else:
                        if (len(n.fanouts)==0):
                            lined = 1
                        else:
                            objfun="C_"+n.name+"_"+n.fanouts[0].name
                            obj_function.append(objfun)
                            line = objfun + ">=0\n"
                            temp.write(line)
                            line = "D_"+n.fanouts[0].name+" - D_"+n.name+">=1\n"
                            temp.write(line)
                            line = "D_"+n.fanouts[0].name+" - D_"+n.name+ "- "+str(N)+" "+objfun+" <= "+ str(N)+"\n"
                            temp.write(line)

            # Equation (2) for splitters
            for s in ntk.splitters:
                for g in s.fanouts:
                    if(g.gate_type!="splitter"):
                        objfun="C_"+s.name+"_"+g.name
                        obj_function.append(objfun)
                        line = objfun + ">=0\n"
                        temp.write(line)
                        line = "D_"+g.name+" - D_"+s.name+">=1\n"
                        temp.write(line)
                        line = "D_"+g.name+" - D_"+s.name+ "- "+str(N)+" "+objfun+" <= "+ str(N)+"\n"
                        temp.write(line)
                for sp in s.splitter_out:
                    objfun="C_"+s.name+"_"+sp.name
                    obj_function.append(objfun)
                    line = objfun + ">=0\n"
                    temp.write(line)
                    line = "D_"+sp.name+" - D_"+s.name+">=1\n" 
                    temp.write(line)
                    line = "D_"+sp.name+" - D_"+s.name+ "- "+str(N)+" "+objfun+" <= "+ str(N)+"\n"
                    temp.write(line)
            # Equation (8)
            for i in range(1, Loutputs + 1):
                temp.write(f"W_{i} >= 0\n")
                # width_constraint = " + ".join([f"X_{n.name}_{i}" for n in ntk.netlist + ntk.splitters])
                width_constraint = " + ".join([f"3 X_{n.name}_{i}" for n in ntk.netlist])
                for n in ntk.splitters:
                    width_constraint += f" + X_{n.name}_{i}"
                width_constraint_buffer = ""
                for n in ntk.netlist:
                    if len(n.splitter_out) == 1:
                        fanout = n.splitter_out[0]
                    elif len(n.fanouts) == 0:
                        continue
                    else:
                        fanout = n.fanouts[0]
                    # ignore cases where level <= ASAP[i] or level > ALAP[j] to reduce complexity
                    # if i <= ASAP[n.name] or i > ALAP[fanout.name]:
                    #     continue
                    edge = (n.name, fanout.name)
                    max_k = k_max[edge]
                    for k in range(1, max_k + 1):
                        width_constraint_buffer += f" + X_{n.name}_{fanout.name}_{k}_{i}"

                for n in ntk.splitters:
                    for fanout in n.fanouts + n.splitter_out:
                        if fanout in n.fanouts and fanout.gate_type == "splitter":
                            continue
                        # ignore cases where level <= ASAP[i] or level > ALAP[j] to reduce complexity
                        # if i <= ASAP[n.name] or i > ALAP[fanout.name]:
                        #     continue
                        edge = (n.name, fanout.name)
                        max_k = k_max[edge]
                        for k in range(1, max_k + 1):
                            width_constraint_buffer += f" + X_{n.name}_{fanout.name}_{k}_{i}"

                width_constraint += width_constraint_buffer
                temp.write(f"{width_constraint} - W_{i} = 0\n")
            # Equation (6)
            for n in ntk.netlist + ntk.splitters:
                level_constraint = " + ".join([f"X_{n.name}_{i}" for i in range(1, Loutputs + 1)])
                temp.write(f"{level_constraint} = 1\n")
            # Equation (7)
                level_assignment = " + ".join([f"{i} X_{n.name}_{i}" for i in range(1, Loutputs + 1)])
                temp.write(f"{level_assignment} - D_{n.name} = 0\n")
            # Equation (9)
            for i in range(2, Loutputs + 1):
                temp.write(f"Width - W_{i} >= 0\n")

            # Equation (20) - (26) for netlist nodes
            for n in ntk.netlist:
                if len(n.splitter_out) == 1:
                    fanout = n.splitter_out[0]
                elif len(n.fanouts) == 0:
                    continue
                else:
                    fanout = n.fanouts[0]
            # for n in ntk.netlist:
            #     for fanout in n.fanouts:
                Write_Equations_20_to_26(ntk, N, Loutputs, n, fanout, temp, ASAP, ALAP, k_max)

            # Equation (20) - (26) for splitters
            for n in ntk.splitters:
                for fanout in n.fanouts + n.splitter_out:
                    if fanout in n.fanouts and fanout.gate_type == "splitter":
                        continue
                    Write_Equations_20_to_26(ntk, N, Loutputs, n, fanout, temp, ASAP, ALAP, k_max)

        filename = "problem.lp"  #ntk.name+"_"+str(N)+".lp"
        #sol_file = "problem_sol.txt" #ntk.name+"_"+str(N)+"_sol.txt"
        lines = []
        with open('temp.txt', 'r') as temp:
            lines = temp.readlines()
        with open(filename,'w') as lp:
            objective = "Minimize\n"
#            for o in obj_function:
#                objective += o + " + "
#            objective += "XNULL;\n"
            objective += "Width\n"
            lp.write(objective)
            for line in lines:
                lp.write(line)
            lp.write("Binary\n")
            for n in ntk.netlist + ntk.splitters:
                for i in range(1, Loutputs + 1):
                    #X_iL is binary
                    lp.write(f"X_{n.name}_{i}\n")
            for n in ntk.netlist:
                # for fanout in n.fanouts:
                if len(n.splitter_out) == 1:
                    fanout = n.splitter_out[0]
                elif len(n.fanouts) == 0:
                    continue
                else:
                    fanout = n.fanouts[0]
                edge = (n.name, fanout.name)
                max_k = k_max[edge]
                for k in range(1, max_k + 1):
                    #C_ijk is binary
                    lp.write(f"C_{n.name}_{fanout.name}_{k}\n")
                    #X_ijkL is binary
                    for L in range(1, ALAP[fanout.name] + 1):
                        lp.write(f"X_{n.name}_{fanout.name}_{k}_{L}\n")
            for n in ntk.splitters:
                for fanout in n.fanouts + n.splitter_out:
                    if fanout in n.fanouts and fanout.gate_type == "splitter":
                        continue
                    edge = (n.name, fanout.name)
                    max_k = k_max[edge]
                    for k in range(1, max_k + 1):
                        #C_ijk is binary
                        lp.write(f"C_{n.name}_{fanout.name}_{k}\n")
                        #X_ijkL is binary
                        for L in range(1, ALAP[fanout.name] + 1):
                            lp.write(f"X_{n.name}_{fanout.name}_{k}_{L}\n")
            lp.write("end")
        ti = time.time()
        os.system("./solve > junk.txt")
        return (time.time()-ti)
    else:
        obj_function=[]
        #bounds = ["Bounds\n"]
        with open('temp.txt', 'w') as temp:
            temp.write("Subject To\n")
            for n in ntk.netlist:
                if (n.gate_type =="PI"):
                    temp.write("D_"+n.name+"=1\n")
                if (n.gate_type=="PO"):
                    temp.write("D_"+n.name+"-D_outputs = 0\n")
                else:
                    if (len(n.splitter_out)==1):
                        objfun="C_"+n.name+"_"+n.splitter_out[0].name
                        obj_function.append(objfun)
                        line = objfun + ">=0\n"
                        temp.write(line)
                        line = "D_"+n.splitter_out[0].name+" - D_"+n.name+">=1\n" 
                        temp.write(line)
                        line = "D_"+n.splitter_out[0].name+" - D_"+n.name+ "- "+str(N)+" "+objfun+" <= "+ str(N)+"\n"
                        temp.write(line)
                    else:
                        if (len(n.fanouts)==0):
                            lined = 1
                        else:
                            objfun="C_"+n.name+"_"+n.fanouts[0].name
                            obj_function.append(objfun)
                            line = objfun + ">=0\n"
                            temp.write(line)
                            line = "D_"+n.fanouts[0].name+" - D_"+n.name+">=1\n"
                            temp.write(line)
                            line = "D_"+n.fanouts[0].name+" - D_"+n.name+ "- "+str(N)+" "+objfun+" <= "+ str(N)+"\n"
                            temp.write(line)
            for s in ntk.splitters:
                for g in s.fanouts:
                    if(g.gate_type!="splitter"):
                        objfun="C_"+s.name+"_"+g.name
                        obj_function.append(objfun)
                        line = objfun + ">=0\n"
                        temp.write(line)
                        line = "D_"+g.name+" - D_"+s.name+">=1\n"
                        temp.write(line)
                        line = "D_"+g.name+" - D_"+s.name+ "- "+str(N)+" "+objfun+" <= "+ str(N)+"\n"
                        temp.write(line)
                for sp in s.splitter_out:
                    objfun="C_"+s.name+"_"+sp.name
                    obj_function.append(objfun)
                    line = objfun + ">=0\n"
                    temp.write(line)
                    line = "D_"+sp.name+" - D_"+s.name+">=1\n" 
                    temp.write(line)
                    line = "D_"+sp.name+" - D_"+s.name+ "- "+str(N)+" "+objfun+" <= "+ str(N)+"\n"
                    temp.write(line)
        filename = "problem.lp"  #ntk.name+"_"+str(N)+".lp"
        #sol_file = "problem_sol.txt" #ntk.name+"_"+str(N)+"_sol.txt"
        lines = []
        with open('temp.txt', 'r') as temp:
            lines = temp.readlines()
        with open(filename,'w') as lp:
            objective = "Minimize\n"
            for o in obj_function:
                objective += o + " + "
            objective += "XNULL;\n"
            lp.write(objective)
            for line in lines:
                lp.write(line)
            lp.write("end")
        ti = time.time()
        os.system("./solve > junk.txt")
        return (time.time()-ti)
def Formulate(ntk,N):
    obj_function=[]
    with open('temp.txt', 'w') as temp:
        for n in ntk.netlist:
            if (n.gate_type =="PI"):
                temp.write("D_"+n.name+"=1;\n")
            if (n.gate_type=="PO"):
                temp.write("D_"+n.name+"=D_outputs;\n")
            else:
                if (len(n.splitter_out)==1):
                    objfun="C_"+n.name+"_"+n.splitter_out[0].name
                    obj_function.append(objfun)
                    line = "1<="+"D_"+n.splitter_out[0].name+" - D_"+n.name+";\n" 
                    temp.write(line)
                    line = "D_"+n.splitter_out[0].name+" - D_"+n.name+ "- "+str(N)+" "+objfun+" <= "+ str(N)+";\n"
                    temp.write(line)
                else:
                    if (len(n.fanouts)==0):
                        lined = 1
                    else:
                        objfun="C_"+n.name+"_"+n.fanouts[0].name
                        obj_function.append(objfun)
                        line = "1<="+"D_"+n.fanouts[0].name+" - D_"+n.name+";\n"
                        temp.write(line)
                        line = "D_"+n.fanouts[0].name+" - D_"+n.name+ "- "+str(N)+" "+objfun+" <= "+ str(N)+";\n"
                        temp.write(line)
        for s in ntk.splitters:
            for g in s.fanouts:
                if(g.gate_type!="splitter"):
                    objfun="C_"+s.name+"_"+g.name
                    obj_function.append(objfun)
                    line = "1<="+"D_"+g.name+" - D_"+s.name+";\n"
                    temp.write(line)
                    line = "D_"+g.name+" - D_"+s.name+ "- "+str(N)+" "+objfun+" <= "+ str(N)+";\n"
                    temp.write(line)
            for sp in s.splitter_out:
                objfun="C_"+s.name+"_"+sp.name
                obj_function.append(objfun)
                line = "1<="+"D_"+sp.name+" - D_"+s.name+";\n" 
                temp.write(line)
                line = "D_"+sp.name+" - D_"+s.name+ "- "+str(N)+" "+objfun+" <= "+ str(N)+";\n"
                temp.write(line)
    filename = ntk.name+"_"+str(N)+".lp"
    sol_file = ntk.name+"_"+str(N)+"_sol.txt"
    lines = []
    with open('temp.txt', 'r') as temp:
        lines = temp.readlines()
    with open(filename,'w') as lp:
        objective = "Min: "
        for o in obj_function:
            objective += o + " + "
        objective += "0;\n"
        lp.write(objective)
        for line in lines:
            lp.write(line)
    os.system("lp_solve "+filename +"> "+sol_file)
def APS(K,N):
    top = K**math.ceil(math.log(N,K))
    bottom = K**math.floor(math.log(N,K))
    if (top==N):
        return top
    else:
        aps = K**math.floor(math.log(N,K))
        aps = aps*math.floor(math.log(N,K))
        while ((K*bottom)+K-1<=N):
            bottom+=K-1
            aps+=1
            aps+=(K-1)*math.ceil(math.log(N,K))
        aps+=(N-bottom)*math.ceil(math.log(N,K))
        aps+=1
        return aps
def calc_cost(n):
    Sumi = 0
    Sumo = 0
    for i in n.inputs:
        Sumi+=(1/len(i.fanouts))
    for o in n.fanouts:
        Sumo+=(1/len(n.fanouts))
    return Sumi-Sumo
def Permutations(sinks):
    perm = []
    if (sinks <=14): #was 15
        for p in range(1,(2**sinks)):
            plocal = []
            order = str(bin(p)[2:])
            while (len(order)<sinks):#add leading 0s
                order =  "0"+order
            i=sinks-1
            for et in order:
                if (et=='1'):
                    plocal.append(i)
                i=i-1
            perm.append(plocal.copy())
    else:
        for p in range(1,(2**14)):
            order = random.randint(1,2**sinks)
            plocal = []
            order = str(bin(order)[2:])
            while (len(order)<sinks):#add leading 0s
                order =  "0"+order
            i=sinks-1
            for et in order:
                if (et=='1'):
                    plocal.append(i)
                i=i-1
            perm.append(plocal.copy())
        
    return perm
                  
def Formulate_init_CPLEX(ntk,N,K):
    
    obj_function=[]
    constraints = 0
    with open('temp.txt', 'w') as temp:
        temp.write("Subject To\nXNULL=0\n")
        for n in ntk.netlist:
            if (n.gate_type =="PI"):
                temp.write("D_"+n.name+"=1\n")
            if (n.gate_type=="PO"):
                temp.write("D_"+n.name+"-D_outputs=0\n")
            else:
                #Smin = APS(K,len(n.fanouts))
                    #Smin = Smin*(len(n.fanouts))
                #S_line = "APS_"+n.name+"=0"
                #APS_min = str(Smin)+"<=APS_"+n.name+";\n"
                spans = []
                for f in n.fanouts:
                    weight = 1/len(n.fanouts)
                    objfun="C_"+n.name+"_"+f.name
                    obj_function.append(str(weight)+" "+objfun)
                    line = objfun + ">=0\n"
                    temp.write(line)
                    line = "D_"+f.name+" - D_"+n.name+">=1\n"
                    temp.write(line)
                    line = "D_"+f.name+" - D_"+n.name+ "- "+str(N)+" "+objfun+ " "+ " <= "+ str(N)+"\n"
                    temp.write(line)
                        #line = "D_"+f.name+" - D_"+n.name+ "- "+str(N)+" "+objfun+ " "+ str(N) + " "+sfun+" <= "+ str(N)+";\n"
                    if (len(n.fanouts)>1):
                        #line = minfanout+"<="+objfun+";\n"
                        #temp.write(line)
                        line = "Span_"+n.name+"_"+f.name+"-D_"+f.name+" + D_"+n.name+" = -1\n"
                        temp.write(line)

                        #line = "1<=S_"+n.name+"_"+f.name+"<="+str(+";\n"
                        #temp.write(line)
                        line = "Span_"+n.name+"_"+f.name+">=1\n"
                        temp.write(line)
                        S_line= "Span_"+n.name+"_"+f.name
                        spans.append(S_line)
                if (len(n.fanouts)>1):
                    perm = Permutations(len(n.fanouts))
                    for subtree in perm:
                        Smin = APS(K,len(subtree))
                        APS_min = ""#str(Smin)
                        for node in subtree:
                            APS_min+=spans[node]+" + "
                        APS_min+="XNULL>= "+str(Smin)+"\n"
                        temp.write(APS_min)
                    #S_line+=";\n"
                    #temp.write(S_line) 
                    #temp.write(APS_min)
    filename = "problem.lp"  #ntk.name+"_"+str(N)+".lp"
    #sol_file = ntk.name+"_"+str(N)+"_sol.txt"
    lines = []
    with open('temp.txt', 'r') as temp:
        lines = temp.readlines()
    with open(filename,'w') as lp:
        objective = "Minimize\n "
        for o in obj_function:
            objective += o + " + "
        objective += "XNULL;\n"
        lp.write(objective)
        for line in lines:
            lp.write(line)
            constraints+=1
        lp.write("end")
    print("Solving Initial Levels with "+ str(constraints)+ " constraints")
    ti = time.time()
    os.system("./solve > junk.txt")#"lp_solve "+filename +"> "+sol_file)
    return (time.time()-ti)













def Read_Solution_CPLEX(ntk,N):
    #print(ntk.s_dict)
    sol_file = "problem_sol.txt"  #ntk.name+"_"+str(N)+"_sol.txt"
    cost = 0
    buff_cost = 0
    buff_cost2=0
    buff_cost3=0
    buff_cost4 = 0
    with open(sol_file,'r') as sol:
        for line in sol:
            if line.split()[1][0]=="C" and len(line.split()[1].split('_')) == 3: #calculate cost
                result = line.split()
                cost += math.ceil(float(result[2]))
                buff_cost += math.ceil((math.ceil(float(result[2]))-1)/2)
                buff_cost2 += math.ceil((math.ceil(float(result[2]))-1)/3)
                buff_cost3 += math.ceil((math.ceil(float(result[2]))-1)/4)
                buff_cost4 += math.ceil((math.ceil(float(result[2]))-1)/5)
            if line.split()[1][0]=="D" and len(line.split()[1].split('_')) == 2: #store depth values
                result = line.split()
                if (result[1].split("_")[1]=="outputs"):
                    continue
                else:
                    if "splitter" in result[1].split("_")[1]: #assign depth value to splitter
                        value = math.ceil(float(result[2]))
                        ntk.splitters[ntk.s_dict[result[1].split("_")[1]]].depth=value
                    else:
                        value = math.ceil(float(result[2]))
                        ntk.Obj(result[1].split("_")[1]).depth =value
                        ntk.Obj(result[1].split("_")[1]).depth_id =value
                        #print(result[0].split("_")[1]+" :" +str(value)) #assign depth value to gate
    cost += len(ntk.splitters)
    buff_cost+=len(ntk.splitters)
    buff_cost2+=len(ntk.splitters)
    buff_cost3+=len(ntk.splitters)
    return cost, [buff_cost,buff_cost2,buff_cost3,buff_cost4]









    

def Gen_Netlist(filename,ntk,phases):
    with open(filename,'w') as file:
        header = "module "+ntk.name+"( "
        inputs = "input "
        outputs="output "
        for i in range(1,phases+1):
            header+="clk_"+str(i)+" , "
        for pi in ntk.PIs:
            header+=pi+" , "
            inputs +=pi+" , "
        for po in ntk.POs:
            header+=po +" , "
            outputs+=po +" , "
        header=header[:-2]+");\n\n"
        file.write(header)
        wire = "wire "
        for w in ntk.wires:
            wire += w + " , "
        for s in ntk.splitters:
            wire += s.name + " , "
        wire = wire[:-2]+";\n\n"
        inputs = inputs[:-2]+";\n"
        outputs = outputs[:-2]+";\n"
        file.write(inputs)
        file.write(outputs)
        file.write(wire)
        for n in ntk.netlist:
            file.write(str(n))
        for s in ntk.splitters:
            file.write(str(s))
        file.write("\nendmodule")

def less(cost,cost_min):
    if (cost[0]<cost_min[0]):
        return True
    elif(cost[0]>cost_min[0]):
        return False
    elif (cost[1]<cost_min[1]):
        return True
    elif (cost[1]>cost_min[1]):
        return False
    elif (cost[2]<cost_min[2]):
        return True
    else:
        return False
def Resolve_Fanouts(ntk,K,init,skip):
    Estimated_cost = 0
    rt=0
    if (init==0):
        for n in ntk.netlist:
            n.Find_Slack(skip)
            #if (n.slack>1):
            #    print(n.name)
        ntk.deleteSplitters()
    for n in ntk.netlist:
        if (len(n.fanouts)<=1):
            continue
        elif(len(n.fanouts)==2):
            s_name = "splitterfrom"+n.name
            split1 = Node(s_name,"splitter",[n],[0])
            ntk.add_splitter(split1)
            #print("Made New Splitter "+str(s_name))
            split1.connect_splitter(n.fanouts,n)
            Estimated_cost+=1
        #elif(len(n.fanouts)<=K and init==1):
         #   s_name = "splitterfrom"+n.name
          #  split1 = Node(s_name,"splitter",[n],[0])
           # ntk.add_splitter(split1)
            #split1.connect_splitter(n.fanouts,n)
            #print("Made New Splitter "+str(s_name))
        else:
            if (init==2):
                #ntk.deleteTree(n.splitter_out[0])
                ti = time.time()
                pt,delays,N = Build_Tree_init(n,K,skip)
                
                #pt,delays,N = Build_Tree(n,K,skip)
                #print("Entering Tree for:"+n.name+" with fanouts:")
                #print(delays)
                rt+= time.time()-ti
                Insert_Tree_init(ntk,pt,[0,N-1,0,0],n,n,delays)
                
                del pt,delays,N
                #print("Exiting with "+str(len(n.fanouts)) + " fanouts")
            else:
                ti =time.time()
                pt,dp,delays,N,cost = Build_Tree_init(n,K,skip)
                #print("Tree time for " + str(len(n.fanouts)) + " Fanouts is %s" % (time.time()-ti))
                rt += time.time()-ti
                #print("Entering Tree Init for:"+n.name+" with fanouts:")
                #print(delays)
                Insert_Tree_init(ntk,pt,[0,N-1,0,0],n,n,delays)
                
                Estimated_cost+=cost[2]
                #if (init==1):
                 #   for f in n.fanouts:
                  #      f.freeze_ASAP=1
                   # for n in ntk.netlist:
                    #    n.Find_ASAP()
                    #ntk.Fix_outputs()
                    #ntk.Set_ALAP()
                    #for n in ntk.netlist:
                     #   n.depth = n.ASAP
                del pt,dp,delays,N
    return rt
    #if (init==1):
     #   print("Estimated Cost after tree: "+str(Estimated_cost))
            
def Build_Tree_init(node,X,phase_skips):
    delays=[]
    N = 0
    recalc=0
    for f in node.fanouts:
        if (f.depth-node.depth-1<0):
            recalc = 1
        delays.append((f.depth-node.depth-1,f.name,f.slack))
        N+=1
    if (recalc==1):
        delays = []
        for f in node.fanouts:
            delays.append((f.depth_id-node.depth_id-1,f.name,f.slack))
    delays = []
    for f in node.fanouts:
        delays.append((1,f.name,0))
    #for f in node.fanouts:
    #    delays.append((f.ALAP-node.ALAP-1,f.name,0))
    #    latest=0
    #    N+=1
    delays.sort()  
    #print(delays)
    Max_d = delays[-1][0]+ 1 + math.ceil(math.log(N,X))
    #print(Max_d)
    if (math.ceil(math.log(N,X))<=0):
        Max_d = delays[-1][0]+ 1+1
    #Max_d = delays[-1][0]+delays[-1][2]+ 1 + math.ceil(math.log(N,X))
    inf = 700000
    dp = [[[[[5000,5000,5000]]*(Max_d+1)]*X]*N]*N
    pt = [[[[(-2,-2,-2)]*(Max_d+1)]*X]*N]*N
    p1 = [N,X]
    dp = numpy.array(dp)
    pt= numpy.array(pt)
    #init
    for s in range(1,min(p1)+1):
        for l in range(1,N-s+2):
            r = l+s-1
            wdelay = delays[l-1][0]
            if (s==1):
                for d in range(0,Max_d+1):
                    delta = abs(d-wdelay)
                    if (d>wdelay):
                        if (d>wdelay+delays[l-1][2]):
                            dp[l-1][l-1][s-1][d] = [delta,delta,0]
                        else:
                            dp[l-1][l-1][s-1][d] = [0,0,0]
                    else:
                        delta = math.floor(float(delta)/phase_skips)
                        dp[l-1][l-1][s-1][d] = [0,0,delta]
            else:
                for el in range(1,3):
                    dp[l-1][r-1][s-1][Max_d][el] = dp[l-1][r-2][s-2][Max_d][el] + dp[r-1][r-1][0][Max_d][el]
                dp[l-1][r-1][s-1][Max_d][0] = max(dp[l-1][r-2][s-2][Max_d][0],dp[r-1][r-1][0][Max_d][0])#,dp[l-1][r-1][s-1][Max_d][1])
    #find min
    for ln in range(1,N):#was 1 to N
        for l in range(1,N-ln+1):
            r = l+ln #check this
            #p2 = [X,ln+1]
            p2 = [X,ln+1]
            d = Max_d-1
            while (d>=0):
                for s in range(1,min(p2)+1):
                    if (s==1):
                        cost_min = [6000000,6000000,600000]
                        #cost_min=numpy.array(cost_min)
                        k_min = 0
                        d_min=0
                        for k in range(1,min(p2)+1):
                            for pr in range(1,phase_skips+1):
                                if (d+pr<=Max_d ):
                                    cost = dp[l-1][r-1][k-1][d+pr].copy()
                                    cost[2]= cost[2]+1
                                    if(less(cost,cost_min)):
                                        for el in range(1,3):
                                            cost_min[el] = cost[el]+0
                                        cost_min[0] = max(cost[0],0)
                                        k_min = k
                                        d_min = d+pr
                        pt[l-1][r-1][s-1][d] = (-1,k_min,d_min)
                        dp[l-1][r-1][s-1][d] = cost_min.copy()
                    else:
                        cost_min = [4000000,4000000,400000]
                        #cost_min=numpy.array(cost_min)
                        p_min = -1
                        k_min = -1
                        #d1_min = -1
                        #d2_min = -1
                        for k in range(1,s):
                            for p in range (l,r-s+k+1):###s+1??
                                cost1 = dp[l-1][p-1][k-1][d].copy()
                                cost2 = dp[p][r-1][s-k-1][d].copy()
                             #   cost1 = dp[l-1][p-1][s-2][d]
                              #  cost2 = dp[p][r-1][0][d]
                                for el in range(1,3):
                                    cost[el] = cost1[el]+cost2[el]
                                cost[0]=max(cost1[0],cost2[0])
                                if (less(cost,cost_min)):
                                    #for el in range(1,3):
                                     #   cost_min[el] = cost1[el]+cost2[el]
                                    cost_min = cost.copy()
                                    #print("Updated")
                                    k_min = k
                                    p_min = p
                        pt[l-1][r-1][s-1][d] = (p_min,k_min,-1)
                        dp[l-1][r-1][s-1][d] = cost_min.copy()

                                #cost1_min = 500000
                                #cost2_min = 500000
                                #d1_ = -1
                                #d2_ = -1
                                #for pr in range(1,phase_skips):
                                 #   cost1 = dp[l-1][p-1][k-1][d+pr]
                                  #  if (cost1<cost1_min):
                                   #     cost1_min = cost1
                                    #    d1_ = d+Pr
                                    #cost2 = dp[p][r-1][s-k-1][d+pr]
                                    #if (cost2<cost2_min):
                d=d-1
    return pt, dp,delays, N, dp[0][N-1][0][0]   



def Insert_Tree_init(ntk,pt,state,root,source, delays):
    step = pt[state[0]][state[1]][state[2]][state[3]]
    if (step[0]==-2):
        print(step)
        print("In state:")
        print(state)
        print("Step:")
        print(step)
    
    if (step[0]==-1):
        next_state = [state[0],state[1],step[1]-1,step[2]]
        if(step[1]>1):
            name = "splitter"+ source.name + "to"+str(delays[state[0]][1])+str(delays[state[1]][1])
            #print(name)
            new_split = Node(name,"splitter",[root],[0])
            #print("Made New Splitter: "+new_split.name)
            #print(len(root.fanouts))
            ntk.add_splitter(new_split)
            #print("Added to Network!!")
            #print(len(root.fanouts))
            if (state[1]-state[0] == step[1]-1):#Fanout to each node
                for s in range(state[0],state[1]+1):
                    sink = ntk.Obj(delays[s][1])
                    new_split.connect_splitter([sink],source)
                    if (state[3]>delays[s][0]):
                        sink.depth = sink.depth+state[3]-delays[s][0]
                        sink.slack = sink.slack -(state[3]-delays[s][0])
                        #print("With Slack:" +str(delays[s][2])+" Retimed "+delays[s][1]+" from "+str(sink.depth-state[3]+delays[s][0])+" to "+str(sink.depth))
                    #print(len(root.fanouts))
            else:
                Insert_Tree_init(ntk,pt,next_state,new_split,source,delays)
        else:
            Insert_Tree_init(ntk,pt,next_state,root,source,delays)
    else:
        next_state = [state[0],step[0]-1,step[1]-1,state[3]]
        next_state2 = [step[0],state[1],state[2]-step[1],state[3]]
        if (state[1]-state[0] == state[2]):#Fanout to each node
            for s in range(state[0],state[1]+1):
                sink = ntk.Obj(delays[s][1])
                root.connect_splitter([sink],source)
                if(state[3]>delays[s][0]):
                    sink.depth = sink.depth+state[3]-delays[s][0]
                    sink.slack = sink.slack -(state[3]-delays[s][0])
                    #print("With Slack:" +str(delays[s][2])+" Retimed " +delays[s][1]+" from "+str(delays[s][0])+" to "+str(state[3]))
        else:
            if (state[0]!=step[0]-1):
                Insert_Tree_init(ntk,pt,next_state,root,source,delays)
            else:
                sink = ntk.Obj(delays[state[0]][1])#left fanout is to 1 node
                #print("Connecting "+root.name + " to "+ sink.name)
                root.connect_splitter([sink],source)
                if (state[3]>delays[state[0]][0]):
                    sink.depth = sink.depth+state[3]-delays[state[0]][0]
                    sink.slack = sink.slack -(state[3]-delays[state[0]][0])
                    #print("With Slack:" +str(delays[state[0]][2])+" Retimed "+delays[state[0]][1]+" from "+str(delays[state[0]][0])+" to "+str(state[3]))
                #print(len(root.fanouts))
            if (state[1]!=step[0]):
                Insert_Tree_init(ntk,pt,next_state2,root,source,delays)
            else: #right fanout is to 1 node
                sink = ntk.Obj(delays[state[1]][1])
                #print("Connecting "+root.name + " to "+ sink.name)
                root.connect_splitter([sink],source)
                if (state[3]>delays[state[1]][0]):
                    sink.depth = sink.depth+state[3]-delays[state[1]][0]
                    sink.slack = sink.slack -(state[3]-delays[state[1]][0])
                    #print("With Slack:" +str(delays[state[1]][2])+" Retimed "+delays[state[1]][1]+" from "+str(delays[state[1]][0])+" to "+str(state[3]))
                #print(len(root.fanouts))
        #   print("Reached Sink:"+str(state[1]))
                                      
                        
                            
                    

def Insert_Buffers(ntk,N,flag,Version):
    if Version:
        sol_file = "problem_sol.txt"  #ntk.name+"_"+str(N)+"_sol.txt"
        if flag == "C":
            with open(sol_file,'r') as sol:
                for line in sol:
                    if line.split()[1][0] == "C":
                        result = line.split()
                        parts = result[1].split('_')
                        # if the line is not c_ijk but is c_ij, then ignore
                        # if the value of c_ijk is 0, then ignore
                        # if len(parts) == 4 and result[2] != "0" and result[2] != "-0":
                        if len(parts) == 4 and int(float(result[2])) != 0:
                            i = parts[1]
                            j = parts[2]
                            k = parts[3]
                            #insert cost buffers between the i and j nodes
                            i_name = i
                            i_first = i_name
                            j_name = j
                            j_first = j_name

                            if k == "1":
                                if "splitter" in i_name and "buf" not in i_name:
                                    i = ntk.splitters[ntk.s_dict[i_name]]
                                else:
                                    i = ntk.Obj(i_name)
                            else:
                                i = ntk.Obj("buf_" + i_first + "_" + j_first + "_" + str(int(k) - 1))

                            if "splitter" in j_name:
                                j=ntk.splitters[ntk.s_dict[j_name]]
                            else:
                                j=ntk.Obj(j_name)

                            buf_name = "buf_" + i_first + "_" + j_first + "_" + k
                            buf = Node(buf_name,"buf",[i],[0])
                            ntk.add(buf)
                            j.insertbuf(i,buf)

        elif flag == "D":
            with open(sol_file,'r') as sol:
                for line in sol:
                    if line.split()[1][0] == "D":
                        result = line.split()
                        parts = result[1].split('_')
                        # if the line is not D_ijk but is D_ij, then ignore
                        # if the value of D_ijk is 0, then ignore
                        # if len(parts) == 4 and result[2] != "0" and result[2] != "-0":
                        if len(parts) == 4 and int(float(result[2])) != 0:
                            i = parts[1]
                            j = parts[2]
                            k = parts[3]
                            value = math.ceil(float(result[2]))
                            buf_name = "buf_" + i + "_" + j + "_" + k
                            buf = ntk.Obj(buf_name)
                            buf.depth = value

    elif Version == 0:
        sol_file = "../problem_sol.txt"  # ntk.name+"_"+str(N)+"_sol.txt"
        with open(sol_file, 'r') as sol:
            for line in sol:
                if (line.split()[1][0] == "C"):  # calculate cost
                    result = line.split()
                    cost = math.ceil(float(result[2]))
                    # insert cost buffers between the i and j nodes
                    i = result[1].split('_')[1]
                    j = result[1].split('_')[2]
                    i_name = i
                    i_first = i_name
                    j_name = j
                    j_first = j_name
                    is_split = 0
                    while (cost > 0):
                        if "splitter" in i_name and "buf" not in i_name:
                            i = ntk.splitters[ntk.s_dict[i_name]]
                        else:
                            i = ntk.Obj(i_name)
                        if "splitter" in j_name:
                            j = ntk.splitters[ntk.s_dict[j_name]]
                        else:
                            j = ntk.Obj(j_name)
                        bufName = "buf_" + i_first + "_" + j_first + "_" + str(cost)
                        buf = Node(bufName, "buf", [i], [0])
                        ntk.add(buf)
                        j.insertbuf(i, buf)
                        buf.depth = i.depth + N
                        i = buf
                        j_name = j.name
                        i_name = i.name
                        cost += -1



import time
def Algorithm(name,fanout,phase_skips,phases):
    circ = Ntk(name)
    start_time= time.time()
    phase_time = 0.0
    tree_time = 0.0
    circ.parse("Notebook_Files/"+name+".v")
    gate_count=0
    for n in circ.netlist:
        if (n.gate_type!="PO" and n.gate_type!="PI"):
            gate_count+=1
    print("Parsed Circuit " +name+" has gate count "+str(gate_count))
    #circ = circuit
    #print("avlie")
    phase_time +=Formulate_init_CPLEX(circ,phase_skips,fanout)
    #print("Total Time: %s seconds " % (phase_time))
    #Formulate_CPLEX(circ,phase_skips)

    best_cost,buff_cost =Read_Solution_CPLEX(circ,phase_skips)

    #for n in circ.netlist:
    #    n.Find_Slack(phase_skips)
    #print("Estimated Cost: "+str(best_cost))
    ######I dont think these were used?? circ.Fix_outputs()
    ######circ.Set_ALAP()
    circ.phases = phases
    #print("Init Trees")
    tree_time+=Resolve_Fanouts(circ,fanout,1,phase_skips)
    circ.Find_maxDepth()
    Loutputs = math.ceil(circ.maxDepth) + 1
    # Loutputs = 38
    print(f"Loutputs: {Loutputs}")
#    Loutputs = 41
    version = 0
    #print("Tree time: %s seconds " % (tree_time))
    #return pt,dp
    #print(len(circ.splitters))
    phase_time+=Formulate_CPLEX(circ,phase_skips,Loutputs, version)
    for n in circ.netlist:
        n.Find_Slack(phase_skips)
    #print("Reading Solution")
    best_cost,buff_cost =Read_Solution_CPLEX(circ,phase_skips)
    cost = 0
    iteration = 1
    saved=[]
    #print("Chain Retiming Cost ="+str(buff_cost))
    print("Initial Cost: "+str(best_cost))
    if (phase_skips==1):
        saved = buff_cost
    while (cost<best_cost):
        for n in circ.netlist:
            n.Find_Slack(phase_skips)
        tree_time+=Resolve_Fanouts(circ,fanout,0,phase_skips)
        #print(len(circ.splitters))
        phase_time+=Formulate_CPLEX(circ,phase_skips, Loutputs, version)
        cost,buff_cost = Read_Solution_CPLEX(circ,phase_skips)
        iteration+=1
        if (cost<best_cost):
            best_cost = cost
            cost = 0
            print("Iteration "+str(iteration)+": "+str(best_cost))
        else:
            print("No Improvement Found in Iteration "+str(iteration) + " at cost "+str(cost))
            # circ.CleanNtk()
            #print("Inserting Buffers")
            # saved = buff_cost
            # Insert_Buffers(circ,phase_skips,"C", version)
            # Insert_Buffers(circ,phase_skips,"D", version)

    version = 1
    cost = 0
    best_cost = math.inf

    # for n in circ.netlist:
    #     n.Find_Slack(phase_skips)
    # tree_time+=Resolve_Fanouts(circ,fanout,0,phase_skips)
    # #print(len(circ.splitters))
    # phase_time+=Formulate_CPLEX(circ,phase_skips, Loutputs, version)
    # cost,buff_cost = Read_Solution_CPLEX(circ,phase_skips)
    # iteration+=1
    #
    # best_cost = cost
    # print("Iteration "+str(iteration)+": "+str(best_cost))
    # circ.CleanNtk()
    # Insert_Buffers(circ,phase_skips,"C", version)
    # Insert_Buffers(circ,phase_skips,"D", version)

    while (cost<best_cost):
        for n in circ.netlist:
            n.Find_Slack(phase_skips)
        tree_time+=Resolve_Fanouts(circ,fanout,0,phase_skips)
        #print(len(circ.splitters))
        phase_time+=Formulate_CPLEX(circ,phase_skips, Loutputs, version)
        cost,buff_cost = Read_Solution_CPLEX(circ,phase_skips)
        iteration+=1
        if (cost<best_cost):
            best_cost = cost
            cost = 0
            print("Iteration "+str(iteration)+": "+str(best_cost))
        else:
            print("No Improvement Found in Iteration "+str(iteration) + " at cost "+str(cost))
            circ.CleanNtk()
            #print("Inserting Buffers")
            saved = buff_cost
            Insert_Buffers(circ,phase_skips,"C", version)
            Insert_Buffers(circ,phase_skips,"D", version)

    #print("Best Cost Found is: "+str(best_cost))
    circ.set_phases()
    netlist_name = name+"_"+str(phases)+"phases_"+str(phase_skips-1)+"_netlist.v"
    Gen_Netlist(netlist_name,circ,phases)
    #print("Generated Netlist: "+netlist_name)
    test =circ.verify(phase_skips)
    # print("n10 node info: \n")
    # print(circ.Obj('n10'))
    # print(circ.Obj('n10').depth)
    # for gate in circ.netlist + circ.splitters:
    #     print("name: "+ gate.name + "; depth: " + str(gate.depth))
    print("Total Time: %s seconds " % (time.time()-start_time))
    print("Time in phase assignment %s " % (phase_time))
    print("Time in tree construction %s " % (tree_time))
    if (not test):
        cost = 10000000
    circ.Print_info()
    return circ,best_cost,saved[0],saved[1],saved[2],saved[3]
def Run_Benchmarks():
    Phase4=[]
    NPhase=[]
    
    circuit = "c2670"
    # circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    exit()
    """
    circuit = "c499"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c880"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c1355"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c1908"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c2670"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c3540"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c5315"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c6288"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    
    circuit = "c7552"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    
    circuit = "mult8"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "counter16"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "counter32"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "counter64"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "counter128"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    
    circuit = "c432"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c499"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c880"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c1355"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c1908"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c2670"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c3540"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c5315"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "c6288"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    
    circuit = "c7552"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    
    circuit = "mult8"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "counter16"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "counter32"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "counter64"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    circuit = "counter128"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,1,4)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    exit()
    circuit = "alu32"
    circ4,cost4,s1,s2,s3,s4 = Algorithm(circuit,4,2,8)
    Phase4.append((cost4,circuit,s1,s2,s3,s4))
    """
    #circuit = "alu32"
    #circuit = "c7552"
    #circ4,cost4,s1,s2,s3 = Algorithm(circuit,4,2,8)
    #Phase4.append((cost4,circuit,s1,s2,s3))
    #circuit = "c2670"
    #circ4,cost4,s1,s2,s3 = Algorithm(circuit,4,3,12)
    #Phase4.append((cost4,circuit,s1,s2,s3))
    #circuit = "c6288"
    #circ4,cost4,s1,s2,s3 = Algorithm(circuit,4,4,16)
    #Phase4.append((cost4,circuit,s1,s2,s3))
    #circuit = "c499"
    #circ4,cost4,s1,s2,s3 = Algorithm(circuit,4,1,4)
    #Phase4.append((cost4,circuit,s1,s2,s3))
    #circuit = "c880"
    #circ4,cost4,s1,s2,s3 = Algorithm(circuit,4,1,4)
    #Phase4.append((cost4,circuit,s1,s2,s3))
    #circuit = "c1355"
    #circ4,cost4,s1,s2,s3 = Algorithm(circuit,4,1,4)
    #Phase4.append((cost4,circuit,s1,s2,s3))
    #circuit = "c1908"
    #circ4,cost4,s1,s2,s3 = Algorithm(circuit,4,1,4)
    #Phase4.append((cost4,circuit,s1,s2,s3))
    #circuit = "c2670"
    #circ4,cost4,s1,s2,s3 = Algorithm(circuit,4,1,4)
    #Phase4.append((cost4,circuit,s1,s2,s3))
    #circuit = "c3540"
    #circ4,cost4,s1,s2,s3 = Algorithm(circuit,4,1,4)
    #Phase4.append((cost4,circuit,s1,s2,s3))
    #circuit = "c5315"
    #circ4,cost4,s1,s2,s3 = Algorithm(circuit,4,1,4)
    #Phase4.append((cost4,circuit,s1,s2,s3))
    #circuit = "c6288"
    #circ4,cost4,s1,s2,s3 = Algorithm(circuit,4,1,4)
    #Phase4.append((cost4,circuit,s1,s2,s3))"""
    return Phase4, NPhase
def print_results(p4,np):
    print("2Skip Results\n_____________")
    total1 = 0
    total2 = 0
    for c in p4:
        print(c[1]+"  |  "+str(c[0]) + " | "+str(c[2]))
        total1 += c[0]
        total2+=c[2]
    print("Sum | "+str(total1) + " | " + str(total2))    
    print("\n\n3-Skip Results\n_____________")
    total3=0
    for c in np:
        print(c[1]+"  |  "+str(c[0]))
        total3+= c[0]
    print("Sum | "+ str(total3))
def print_results2(p4):
    total0=0
    total1=0
    total2=0
    total3=0
    total4=0
    for c in p4:
        print(c[1]+" | "+str(c[0]) + " | " + str(c[2]) + " | " +str(c[3]) + " | " + str(c[4]) + " | " + str(c[5]))
        total0+= c[0]
        total1+= c[2]
        total2+= c[3]
        total3+= c[4]
        total4+= c[4]
    print("Sum | "+str(total0) + " | " + str(total1) + " | " + str(total2) + " | " + str(total3)+ " | " + str(total4))    
def string_to_file(string,path):
    with open(path,'w') as f:
        f.write(string)
def file_to_string(path):
    with open(path,'r') as f:
        return f.read()
  
p4,np = Run_Benchmarks()
print_results2(p4)
#path = "Notebook_Files/counter16.v"
#string_to_file(file_to_string(path).replace("_",""),path)
#path = "Notebook_Files/counter32.v"
#string_to_file(file_to_string(path).replace("_",""),path)
#path = "Notebook_Files/counter64.v"
#string_to_file(file_to_string(path).replace("_",""),path)
#path = "Notebook_Files/counter128.v"
#string_to_file(file_to_string(path).replace("_",""),path)
#Algorithm("c7552",4,1,4)
#Algorithm("c7552",4,2,8)
