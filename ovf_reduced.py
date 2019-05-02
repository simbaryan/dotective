"""
@author: Simba Ryan
Mumax3 OVF
"""

#import pandas as pd
import numpy as np
import struct
#import matplotlib.pyplot as plt
#import matplotlib.cm as cm
#import os, os.path

class OVF:
    
    def __init__(self, folder, file_name):
        self.Nx, self.Ny, self.Nz = 0, 0, 0
        self.dx, self.dy, self.dz = 0, 0, 0
        self.xsize, self.ysize, self.zsize = 0, 0, 0
        self.name = file_name
        self.headerBytes = 0
        self.fieldIndex = -1
        self.averagingIndex = -1
        self.initialOrientation = False         
        self.filePath = folder + '/' + file_name
        self.folder = folder
        
        self.read_header()
        
        #initialize numpy array for the m components
        self.m = np.empty([self.Ny, self.Nx], dtype = [('mx',float), ('my',float), ('mz',float)])
        return   
    
    
    def read_header(self):
        """Reads the header of the OVF at file_path, extracting variables and counting the bytes until the data starts."""
        #self.name = file_path.split('\\')[-1].split('.ovf')[0]      
        
        #Dictionary to relate header lines to object properties
        varDictFlt = {'# xmax': 'xsize', '# ymax': 'ysize', '# zmax': 'zsize'}
        varDictFlt.update({'# xstepsize': 'dx', '# ystepsize': 'dy', '# zstepsize': 'dz'})
        varDictInt = {'# xnodes': 'Nx', '# ynodes': 'Ny', '# znodes': 'Nz'}
        
                        
        with open(self.filePath, "rb") as OVFfile:
            while self.headerBytes < 10000:
                try:
                    newLine = OVFfile.readline()
                    self.headerBytes += len(newLine)
                    if newLine.decode() == '# Begin: Data Binary 4\n':
                        break
                    
                    #Fill in the relevant variables from the header
                    lineSplit = newLine.decode().split(': ')
                    
                    try:
                        ovfProperty = varDictInt[lineSplit[0]]
                        setattr(self, ovfProperty, int(lineSplit[1])) 
                    except:
                        pass
                    try:
                        ovfProperty = varDictFlt[lineSplit[0]]
                        setattr(self, ovfProperty, float(lineSplit[1]))
                    except:
                        continue #line read wasn't of interest (i.e. in any dictionary)
                        
                except:
                    print("Couldn't find end of header!")
        return self.headerBytes
    
    def read_m_data(self):
        """Creates a numpy array that has the components of magnetization extracted from the ovf file"""
        
        with open(self.filePath, "rb") as file:
            file.seek(self.headerBytes)
            #check that the first four bytes are the OOMMF check value
            if struct.unpack('f', file.read(4))[0] != 1234567.0:
                print("Check byte was not found in file: " + self.name)
                return
            
            #read in the components of the magnetization, assuming only one pixel in z for now!!!!!!
            for j in range(0, self.Ny):
                for i in range(0, self.Nx):
                    for c in range(0,3):
                        fltBytes = file.read(4)
                        self.m[(self.Ny-1) - j, i][c] = struct.unpack('f', fltBytes)[0] #stack from the bottom up in y 
        return
    
    def get_elements_by_index(self, index, element_type = 'cell'):
        ''' Returns the magnetization vector(s) for a 'cell', 'row', or 'column' in the ovf file. Index must be (row, column) for 'cell',
        and an integer for 'row' or 'column'.'''
        if element_type != 'cell' and element_type != 'row' and element_type != 'column':
            element_type = 'cell' #make sure an incorrect value doesn't mess anything up
        
        if element_type == 'cell':
            return self.m[index[0],index[1]]
        
        if element_type == 'row':
            return self.m[int(index), :]
        
        if element_type == 'column':
            return self.m[:, int(index)]
        
                
    def get_elements_by_position(self, position, element_type = 'cell'):
        ''' Returns the magnetization vector(s) for a 'cell', 'row', or 'column' in the ovf file. Position must be (x,y) for 'cell',
        and an single value for 'row' or 'column'.'''
        if element_type != 'cell' and element_type != 'row' and element_type != 'column':
            element_type = 'cell' #make sure an incorrect value doesn't mess anything up
        
        if element_type == 'cell':
            xVal = position[0]
            yVal = position[1]
            row = yVal / self.dy - 1.0 / 2.0 * (1 - self.Ny)
            col = xVal / self.dx - 1.0 / 2.0 * (1 - self.Nx)
            return self.m[int(row), int(col)]
        
        if element_type == 'row':
            yVal = position
            row = yVal / self.dy - 1.0 / 2.0 * (1 - self.Ny)
            return self.m[int(row), :]
        
        if element_type == 'column':
            xVal = position
            col = xVal / self.dx - 1.0 / 2.0 * (1 - self.Nx)
            return self.m[:, int(col)]
