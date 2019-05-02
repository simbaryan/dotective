print("START @", now())

////////////////////////////////////////////////////////////
//World Settings////////////////////////////////////////////

//Dimensions of sample in m
lx := 20e-6; //Cell size will be ~ 19.53nm
ly := 20e-6;
lz := 20e-9;

//Number of cells
nx := 1024;
ny := 1024;
nz := 1;

//Cell dimensions in m
dx := lx/nx;
dy := ly/ny;
dz := lz/nz;

//Periodic boundary conditions
pbcx := 2
pbcy := 2
pbcz := 0

//Grid size, cell size, and PBC
SetGridSize(nx,ny,nz)
SetCellSize(dx,dy,dz)
SetPBC(pbcx,pbcy,pbcz)

////////////////////////////////////////////////////////////
//Material Settings/////////////////////////////////////////

fpMeff := 2370; //4piMeff in G
fpMs := 1700; //4piMs in G
Mconv := 1000/(4*pi); //Conversion to SI (A/m)
NotMumaxAlpha:= 1e-3; //Variable to get around errors

//Mumax-specific settings
Msat = fpMs*Mconv; //Saturation mag
Ku1 = fpMs*Mconv/2*(fpMs-fpMeff)*Mconv*mu0; //Uniaxial constant in J/m^3
anisU = vector(0,0,1) //Uniaxial anisotropy direction
Aex = 3.65e-12; //Exchange stiffness in J/T
alpha = NotMumaxAlpha; //Gilbert damping

//Define cleaver region with complete area denial
cutx:= 11e-6; //Position of region center in m
cutw:= 10e-6; //Width of region in m
DefRegion(1, xrange(-cutw/2 + cutx, cutw/2 + cutx))
alpha.SetRegion(1, 1) //Typical value ~ 0.0012700025316455697
aex.SetRegion(1, 0) //Typical value ~ 4.3e-12
Msat.SetRegion(1, 0) //Typical value ~ 135282.0
Ku1.SetRegion(1, 0) //Typical value ~ -5208.345512682275

//Turn on magnetization averaging by setting this to a non-zero number (WARNING: Slows down processing, potentially a lot!)
avgBy := 0 //Typical value = 8.0

m = uniform(0,0,1) //Initial magnetization

////////////////////////////////////////////////////////////
//Microwave Settings////////////////////////////////////////

A1 := 1e-6; //Amplitude in T
fr := 2e9; //Frequency in Hz
wr := 2*pi*fr; //Angular frequency

////////////////////////////////////////////////////////////
//External Field Settings///////////////////////////////////

dH := 1*1e-4; //Step size

//Full range = 3070->3250
initB := 3165*1e-4;
stopB := 3186*1e-4;

fieldSteps := ceil((stopB-initB)/dH);

////////////////////////////////////////////////////////////
//The 'Quantum Dot' Region (dipole field)///////////////////

px := 0;
pz := 4.25e-6;
pm := -4.48e-12; //Probe moment in J/T
ppos := Vector(px, 0, pz);
pvec := Vector(0, 0, pm);

pmask := NewSlice(3, nx, ny, 1)

m0 := 1e-7; //Mu0/4pi = 1e-7
for i:=0; i<nx; i++ {
	for j:=0; j<ny; j++ {
		r := index2coord(i, j, 0) //Vector from origin to pixel
		dr := r.Sub(ppos) //Vector pointing from moment to pixel
		rmag := dr.len()
		term1 := dr.Mul(pvec.Dot(dr)*3*m0/pow(rmag,5))
		term2 := pvec.Mul(-m0/pow(rmag,3))
		pfield := term1.Add(term2)
		pmask.SetVector(i, j, 0, pfield)
	}
}
B_ext.Add(pmask, 1)

////////////////////////////////////////////////////////////
//Field Sweep Setup/////////////////////////////////////////

//Keep track of field values and associated data file numbers
dM := 0.0;
currB := initB
count := 0;
TableAddVar(dM, "dM", "")
TableAddVar(currB, "Hext", "T")
TableAddVar(count, "FieldNum", "")

T1ns := ceil(1/(NotMumaxAlpha*wr)*1e9); //Round T1 up in nanoseconds
tau := T1ns*1e-9; //Simulate this much real time
print("T1ns=",T1ns)
print("tau=",tau)

//External field
B_ext = Vector(0, 0, initB)

//Relax system before starting sweeps
//relax()

////////////////////////////////////////////////////////////
//Field Sweep///////////////////////////////////////////////

print("Initial Field:", initB)

for i:=0; i<fieldSteps; i++ {
	print("Started field step", i+1, "out of", fieldSteps, "------")
	print(" * Current field:", currB)
	
	FixDt = 0 //Disable fixed time steps
	
	//Set the external field, relax magnetization to lowest possible energy state, and save the initial state
	B_ext = Vector(0, 0, currB)
	relax()
	saveas(m, sprint(i,"-m0"))

	//Get reduced magnetization (at center of dot)
	Mx := nx/2
	My := ny/2
	Mz := 0
	M0 := Vector(m.GetCell(Mx, My, Mz).X(), m.GetCell(Mx, My, Mz).Y(), m.GetCell(Mx, My, Mz).Z())

	//Add in MW field, simulate for the time calculated above, and save the evolved state
	B_ext = Vector(0, A1*sin(wr*t), currB)
	run(tau)
	saveas(m, sprint(i,"-f1-0"))

	//Magnetization averaging (NOTE: Must be enabled in settings above)
	if(avgBy != 0) {
		FixDt = 1/(avgBy*fr)/10 + 1e-15 //set time step to 10 steps per 1/8 period (plus small amount)

		for j:=1; j<avgBy; j++ {
			run(1/(avgBy*fr))
			saveas(m, sprint(i,"-f1-",j))
		}
	}
	
	//Get final change in M (at center of dot)
	Mf := Vector(m.GetCell(Mx, My, Mz).X(), m.GetCell(Mx, My, Mz).y(), m.GetCell(Mx, My, Mz).z())
	dM = 1.0-Mf.dot(M0)

	//Save current table data
	TableSave()
	count += 1

	//Update the external field
	currB += dH
	currB = trunc(currB*1e4)*1e-4 //Fix MuMax's dumb adding

	print(" * Final dM at (", Mx, ",", My, ",", Mz, "):", dM)
	print(" * Finished step at:", now())
}

print("ENDED @", now())