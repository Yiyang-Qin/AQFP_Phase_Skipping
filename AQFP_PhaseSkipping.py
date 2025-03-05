import random
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
        elif(self.freeze_ASAP==0):
            temp=1
            for i in self.inputs:
                if (i.ASAP+1>temp):
                    temp = i.ASAP+1
            self.ASAP=temp
    def Find_ALAP(self):
        if (len(self.fanouts)==0 or len(self.inputs)==0):
            self.ALAP=self.ASAP
        else:
            temp = 999999
            for o in self.fanouts:
                if (o.ALAP-1<temp):
                    temp = o.ALAP-1
            self.ALAP = temp
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
            # index = 0
            # count = -1
            # for i in f.inputs:
            #     count+=1
            #     if (i.name == self.name):
            #         index = count
            # f.splitter_in[index] = 0
            for index in range(len(f.splitter_in)):
                if f.splitter_in[index] != 0 and f.splitter_in[index].name == self.name:
                    f.splitter_in[index] = 0
                    break
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
        # print("deleteTree called upon: ", splitter_root.name)

        for s in splitter_root.splitter_out:
            self.deleteTree(s)

        # if splitter_root.name == "splittern53ton54n64":
        #     print(splitter_root)
        #     print("splittern53ton54n64's inputs: ")
        #     for i in splitter_root.inputs:
        #         print(i)
        #     for i in self.netlist:
        #         if i.name == "n54":
        #             print("fanouts length: ", len(i.fanouts))
        #             print("n54's splitter_in:")
        #             print(i.splitter_in)
        #             for j in i.splitter_in:
        #                 if j != 0:
        #                     print(j.name)
        #             print("n54's input:")
        #             for j in i.inputs:
        #                 if j != 0:
        #                     print(j.name)
        #         if i.name == "n57":
        #             print("n57's splitter_in:")
        #             for j in i.splitter_in:
        #                 if j != 0:
        #                     print(j.name)
        #             print("n57's inputs:")
        #             for j in i.inputs:
        #                 if j != 0:
        #                     print(j.name)
        #         if i.name == "n61":
        #             print("n61's splitter_in:")
        #             for j in i.splitter_in:
        #                 if j != 0:
        #                     print(j.name)
        #             print("n61's inputs:")
        #             for j in i.inputs:
        #                 if j != 0:
        #                     print(j.name)
        #         if i.name == "n64":
        #             print("n64's splitter_in:")
        #             for j in i.splitter_in:
        #                 if j != 0:
        #                     print(j.name)
        #             print("n64's inputs:")
        #             for j in i.inputs:
        #                 if j != 0:
        #                     print(j.name)
            # for j in splitter_root.fanouts:
            #     print(j.name)
        splitter_root.reset_splitters()
        # if splitter_root.name == "splittern53ton54n64":
        #     for i in self.netlist:
        #         if i.name == "n54":
        #             print("fanouts length: ", len(i.fanouts))
        #             print("n54's splitter_in:")
        #             for j in i.splitter_in:
        #                 if j != 0:
        #                     print(j.name)
        splitter_root.inputs[0].splitter_out.remove(splitter_root)

        # if len(self.splitters) != len(self.s_dict):
        #     print("WARNING: splitters and s_dict number mismatch: ", len(self.splitters), "vs.", len(self.s_dict))
        #
        # for j in self.s_dict:
        #     if self.splitters[self.s_dict[j]].name != j:
        #         print("Number ", self.s_dict[j], ":", self.splitters[self.s_dict[j]].name, " vs. ", j)

        if splitter_root in self.splitters:
            index_to_remove = self.s_dict[splitter_root.name]
            # Remove the splitter from the list and s_dict
            self.splitters.pop(index_to_remove)
            del self.s_dict[splitter_root.name]
            # Update indices of splitters after the removed one
            for i in range(index_to_remove, len(self.splitters)):
                self.s_dict[self.splitters[i].name] = i

        # # self.splitters.pop(self.s_dict[splitter_root.name])
        # if splitter_root in self.splitters:
        #     self.splitters.remove(splitter_root)
        #     del self.s_dict[splitter_root.name]
        #     # del splitter_root

    def Print_depths(self):
        for n in self.netlist:
            print(n.name + " : " +str(n.depth))
        for s in self.splitters:
            print(s.name + ": " + str(s.depth))
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
                    # # print(n.splitter_in)
                    # # print(n.splitter_out)
                    # print("fanouts length: ", len(i.fanouts))
                    # print("splitter_in:")
                    # for j in n.splitter_in:
                    #     if j != 0:
                    #         print(j.name)
                    # # for j in n.splitter_out:
                    # #     print(j.name)
                    # print("inputs:")
                    # for j in n.inputs:
                    #     print(j.name)
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

def Formulate_CPLEX(ntk,N):
    obj_function=[]
    with open('temp.txt','w') as temp:
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
    filename = "problem.lp" 
    lines = []
    with open('temp.txt','r') as temp:
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
    os.system("./solve > Cplex_output.txt")
    return (time.time()-ti)
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
    if (sinks <=14): 
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
    with open('temp.txt','w') as temp:
        temp.write("Subject To\nXNULL=0\n")
        for n in ntk.netlist:
            if (n.gate_type =="PI"):
                temp.write("D_"+n.name+"=1\n")
            if (n.gate_type=="PO"):
                temp.write("D_"+n.name+"-D_outputs=0\n")
            else:
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
                    if (len(n.fanouts)>1):
                        line = "Span_"+n.name+"_"+f.name+"-D_"+f.name+" + D_"+n.name+" = -1\n"
                        temp.write(line)
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
    filename = "problem.lp" 
    lines = []
    with open('temp.txt','r') as temp:
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
    os.system("./solve > Cplex_output.txt")#"lp_solve "+filename +"> "+sol_file)
    return (time.time()-ti)













def Read_Solution_CPLEX(ntk,N):
    #print(ntk.s_dict)
    sol_file = "problem_sol.txt"#ntk.name+"_"+str(N)+"_sol.txt"
    cost = 0
    buff_cost = 0
    buff_cost2=0
    buff_cost3=0
    buff_cost4 = 0
    with open(sol_file,'r') as sol:
        for line in sol:
            if (line.split()[1][0]=="C"): #calculate cost
                result = line.split()
                cost += math.ceil(float(result[2]))
                buff_cost += math.ceil((math.ceil(float(result[2]))-1)/2)
                buff_cost2 += math.ceil((math.ceil(float(result[2]))-1)/3)
                buff_cost3 += math.ceil((math.ceil(float(result[2]))-1)/4)
                buff_cost4 += math.ceil((math.ceil(float(result[2]))-1)/5)
            if (line.split()[1][0]=="D"): #store depth values
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

import matplotlib.pyplot as plt
from collections import Counter
import random

def analyze_fanout_distribution(ntk):
    fanout_lengths = [len(n.fanouts) for n in ntk.netlist]

    # Print basic statistics
    print("Fanout Distribution Statistics:")
    print(f"Total Nodes: {len(fanout_lengths)}")
    print(f"Max Fanouts: {max(fanout_lengths)}")
    print(f"Min Fanouts: {min(fanout_lengths)}")
    print(f"Average Fanouts: {sum(fanout_lengths) / len(fanout_lengths):.2f}")

    # Count occurrences of each fanout length
    fanout_counts = Counter(fanout_lengths)

    # Sort keys for plotting
    keys = sorted(fanout_counts.keys())
    values = [fanout_counts[k] for k in keys]

    # Plot histogram
    plt.figure(figsize=(10, 5))
    plt.bar(keys, values, width=0.8, color='blue', alpha=0.7)
    plt.xlabel("Number of Fanouts")
    plt.ylabel("Number of Nodes")
    plt.title("Distribution of Fanout Counts in Netlist")
    plt.xticks(keys)
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    plt.show()

# Call this function after loading the netlist
# Example usage:
# analyze_fanout_distribution(your_ntk_object)

def Resolve_Fanouts(ntk,K,init,skip):
    # print("-------------------------Resolve_Fanouts called------------------------------")
    Estimated_cost = 0
    rt=0
    if (init==0):
        for n in ntk.netlist:
            n.Find_Slack(skip)
        ntk.deleteSplitters()

    ###--------------------------VERSION1:50% chance of deletion until reach threshold------------------------------###
    # num_splitters_threshold = int(0.5*len(ntk.splitters))
    # for n in ntk.netlist:
    #     if random.random() < 0.5: # 50% probability
    #         for s in n.splitter_out:
    #             ntk.deleteTree(s)
    #         if len(ntk.splitters) < num_splitters_threshold:
    #             break

    ###--------------------------VERSION2:random shuffle deletion until reach threshold------------------------------###
    # num_splitters_threshold = int(0.75 * len(ntk.splitters))
    # # Shuffle netlist to process nodes in random order
    # randomized_netlist = random.sample(ntk.netlist, len(ntk.netlist))
    # for n in randomized_netlist:
    #     for s in n.splitter_out:
    #         ntk.deleteTree(s)
    #     if len(ntk.splitters) < num_splitters_threshold:
    #         break

    ###--------------------------VERSION3:delete node with fanouts < percentils------------------------------###
    # fanout_lengths = sorted([len(n.fanouts) for n in ntk.netlist])
    # fanout_threshold = numpy.percentile(fanout_lengths, 95)
    # print("fanout_threshold = ", fanout_threshold)
    # # fanout_threshold = 6
    # for n in ntk.netlist:
    #     if len(n.fanouts) <= fanout_threshold:
    #         for s in n.splitter_out:
    #             ntk.deleteTree(s)

    for n in ntk.netlist:
        if not n.splitter_out:
            if (len(n.fanouts)<=1):
                continue
            elif(len(n.fanouts)==2):
                s_name = "splitterfrom"+n.name
                split1 = Node(s_name,"splitter",[n],[0])
                ntk.add_splitter(split1)
                split1.connect_splitter(n.fanouts,n)
                Estimated_cost+=1
            else:
                ti =time.time()
                pt,dp,delays,N,cost = Build_Tree_init(n,K,skip)
                rt += time.time()-ti
                Insert_Tree_init(ntk,pt,[0,N-1,0,0],n,n,delays)
                Estimated_cost+=cost[2]
                del pt,dp,delays,N
    return rt
            
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
    delays.sort()  
    Max_d = delays[-1][0]+ 1 + math.ceil(math.log(N,X))
    if (math.ceil(math.log(N,X))<=0):
        Max_d = delays[-1][0]+ 1+1
    inf = 700000
    dp = [[[[[5000,5000,5000]]*(Max_d+1)]*X]*N]*N
    pt = [[[[(-2,-2,-2)]*(Max_d+1)]*X]*N]*N
    p1 = [N,X]
    dp = numpy.array(dp)
    pt= numpy.array(pt)
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
                dp[l-1][r-1][s-1][Max_d][0] = max(dp[l-1][r-2][s-2][Max_d][0],dp[r-1][r-1][0][Max_d][0])
    for ln in range(1,N):
        for l in range(1,N-ln+1):
            r = l+ln 
            p2 = [X,ln+1]
            d = Max_d-1
            while (d>=0):
                for s in range(1,min(p2)+1):
                    if (s==1):
                        cost_min = [6000000,6000000,600000]
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
                        p_min = -1
                        k_min = -1
                        for k in range(1,s):
                            for p in range (l,r-s+k+1):
                                cost1 = dp[l-1][p-1][k-1][d].copy()
                                cost2 = dp[p][r-1][s-k-1][d].copy()
                                for el in range(1,3):
                                    cost[el] = cost1[el]+cost2[el]
                                cost[0]=max(cost1[0],cost2[0])
                                if (less(cost,cost_min)):
                                    cost_min = cost.copy()
                                    k_min = k
                                    p_min = p
                        pt[l-1][r-1][s-1][d] = (p_min,k_min,-1)
                        dp[l-1][r-1][s-1][d] = cost_min.copy()
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
            new_split = Node(name,"splitter",[root],[0])
            ntk.add_splitter(new_split)
            if (state[1]-state[0] == step[1]-1):#Fanout to each node
                for s in range(state[0],state[1]+1):
                    sink = ntk.Obj(delays[s][1])
                    new_split.connect_splitter([sink],source)
                    if (state[3]>delays[s][0]):
                        sink.depth = sink.depth+state[3]-delays[s][0]
                        sink.slack = sink.slack -(state[3]-delays[s][0])
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
        else:
            if (state[0]!=step[0]-1):
                Insert_Tree_init(ntk,pt,next_state,root,source,delays)
            else:
                sink = ntk.Obj(delays[state[0]][1])#left fanout is to 1 node
                root.connect_splitter([sink],source)
                if (state[3]>delays[state[0]][0]):
                    sink.depth = sink.depth+state[3]-delays[state[0]][0]
                    sink.slack = sink.slack -(state[3]-delays[state[0]][0])
            if (state[1]!=step[0]):
                Insert_Tree_init(ntk,pt,next_state2,root,source,delays)
            else: #right fanout is to 1 node
                sink = ntk.Obj(delays[state[1]][1])
                root.connect_splitter([sink],source)
                if (state[3]>delays[state[1]][0]):
                    sink.depth = sink.depth+state[3]-delays[state[1]][0]
                    sink.slack = sink.slack -(state[3]-delays[state[1]][0])
                                      
                        
                            
                    

def Insert_Buffers(ntk,N):
    sol_file = "problem_sol.txt"#ntk.name+"_"+str(N)+"_sol.txt"
    with open(sol_file,'r') as sol:
        for line in sol:
            if (line.split()[1][0]=="C"): #calculate cost
                result = line.split()
                cost = math.ceil(float(result[2]))
                #insert cost buffers between the i and j nodes
                i = result[1].split('_')[1]
                j = result[1].split('_')[2]
                i_name = i
                i_first = i_name
                j_name = j
                j_first = j_name
                is_split = 0
                while(cost>0):
                    if "splitter" in i_name and "buf" not in i_name:
                        i = ntk.splitters[ntk.s_dict[i_name]]
                    else: 
                        i = ntk.Obj(i_name)
                    if "splitter" in j_name:
                        j=ntk.splitters[ntk.s_dict[j_name]]
                    else:
                        j=ntk.Obj(j_name)
                    bufName = "buf_"+i_first+"_"+j_first+"_"+str(cost)
                    buf = Node(bufName,"buf",[i],[0])
                    ntk.add(buf)
                    j.insertbuf(i,buf)
                    buf.depth = i.depth+N
                    i = buf
                    j_name = j.name
                    i_name = i.name
                    cost += -1

import time
def Algorithm(name,fanout,phase_overlaps,phases):
    circ = Ntk(name)
    start_time= time.time()
    phase_time = 0.0
    tree_time = 0.0
    circ.parse("Benchmark_Files/"+name+".v")
    gate_count=0
    for n in circ.netlist:
        if (n.gate_type!="PO" and n.gate_type!="PI"):
            gate_count+=1
    print("\nParsed Circuit " +name+" has gate count "+str(gate_count))
    phase_time +=Formulate_init_CPLEX(circ,phase_overlaps,fanout)
    best_cost,buff_cost =Read_Solution_CPLEX(circ,phase_overlaps)
    circ.phases = phases
    Print_Fanout_Flag = 0 # set when generating the fanouts distribution plot
    if Print_Fanout_Flag:
        analyze_fanout_distribution(circ)
        return circ, 0
    tree_time+=Resolve_Fanouts(circ,fanout,1,phase_overlaps)
    phase_time+=Formulate_CPLEX(circ,phase_overlaps)
    for n in circ.netlist:
        n.Find_Slack(phase_overlaps)
    best_cost,buff_cost =Read_Solution_CPLEX(circ,phase_overlaps)
    cost = 0
    iteration = 1
    saved=[]
    while (cost<best_cost):
        for n in circ.netlist:
            n.Find_Slack(phase_overlaps)

        tree_time+=Resolve_Fanouts(circ,fanout,0,phase_overlaps)

        phase_time+=Formulate_CPLEX(circ,phase_overlaps)
        cost,buff_cost = Read_Solution_CPLEX(circ,phase_overlaps)
        iteration+=1
        if (cost<best_cost):
            best_cost = cost
            cost = 0
        else:
            print("No Improvement Found in Iteration "+str(iteration) + " at cost "+str(cost))

            circ.CleanNtk()
            print("Inserting Buffers")
            saved = buff_cost
            Insert_Buffers(circ,phase_overlaps)
    circ.set_phases()
    # netlist_name = name+"_"+str(phases)+"phases_"+str(phase_overlaps-1)+"_netlist.v"
    # Gen_Netlist(netlist_name,circ,phases)
    # print("Generated Netlist: "+netlist_name)
    test =circ.verify(phase_overlaps)
    print("Total Time: %s seconds " % (time.time()-start_time))
    print("Time in phase assignment %s " % (phase_time))
    print("Time in tree construction %s \n\n" % (tree_time))
    if (not test):
        cost = 10000000
    return circ,best_cost
def Run_Benchmarks(Names,fanout_limit,phase_skips,phases):
    Results =[]
    for s in Names:
    	circuit = s
    	circ,cost = Algorithm(circuit,fanout_limit,phase_skips+1,phases)
    	Results.append([cost,circuit])
    print_results(Results,fanout_limit,phase_skips,phases)
def print_results(Results,fanout_limit,phase_skips,phases):
    print("Parameters")
    print("Phases:"+str(phases)+"\nMaximum Phase Skips:"+str(phase_skips)+"\nSplitter Fanout Limit:"+str(fanout_limit))
    print("\n\nSummary of Results\nBenchmark | Total Buffer/Splitter Cost")
    for c in Results:
        print(c[1]+"  |  "+str(c[0]))
  
     
def string_to_file(string,path):
    with open(path,'w') as f:
        f.write(string)
def file_to_string(path):
    with open(path,'r') as f:
        return f.read()


##############Modify HERE##########
# Benchmarks = ["c432","c499","c880","c1355","c1908","c2670"]
# Benchmarks = ["c6288", "alu32", "c7552"]
Benchmarks = ["c7552"]
Splitter_Fanout = 4
Phase_Skips = 1
Phases  = 8
##############
print("A Joint Optimization of Buffer and Splitter Insertion")
print("Running Benchmarks:")
print(Benchmarks)
Run_Benchmarks(Benchmarks,Splitter_Fanout,Phase_Skips,Phases)


