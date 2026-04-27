from .specdata import SpectroscopicData, PartitionFunction
from astropy.table import Table
from scipy.interpolate import interp1d
from astropy.io import ascii

pf_filename = {
    "JPL": "./database/catdir.cat",
    "CDMS": "./database/partition_function.dat"
}

def get_JPL_table(filename):
    with open(filename, "r") as f:
        data = f.read()

    lines = data.split("\n")
    def tryfloat(x):
            try:
                return float(x)
            except ValueError:
                return np.nan

    tbl = ascii.read(
        filename,
        format="fixed_width",
        names=['tag', 'name', '#lines', 'lg(Q(300))', 'lg(Q(225))',
                            'lg(Q(150))', 'lg(Q(75))', 'lg(Q(37.5))', 'lg(Q(18.75))', 'lg(Q(9.375))', "version"],
        col_starts=(0, 7, 19, 26, 33, 40, 47, 54, 61, 68, 75),
    )
    # tbl = Table(tbl_rows)
    return tbl

def fetch_JPL_species():
    tbl = get_JPL_table(JPL_PF_filename)
    df_mol = tbl["tag", "name"].to_pandas()
    df_mol["catalog"] = "JPL"
    return df_mol

def read_JPL_partition_function(filename, tag):
    tbl = get_JPL_table(filename)

    temps = np.array([300, 225, 150, 75, 37.5, 18.75, 9.375])
    Qvals = tbl[tbl["tag"] == tag]
    Qvals = np.array(list(Qvals[0])[3:-1])
    # print(tbl)
    return temps[~np.isnan(Qvals)], 10 ** Qvals[~np.isnan(Qvals)]

def get_CDMS_table(filename):
    with open(filename, "r") as f:
        data = f.read()

    lines = data.split("\n")
    def tryfloat(x):
            try:
                return float(x)
            except ValueError:
                return np.nan

    # the 'fixed width' table reader fails because there are rows that violate fixed width
    tbl_rows = []
    for row in lines[4:-2]:
        split = row.split()
        tag = int(split[0])
        molecule_and_lines = row[7:41]
        molecule = " ".join(molecule_and_lines.split()[:-1])
        nlines = int(molecule_and_lines.split()[-1])
        partfunc = map(tryfloat, row[41:].split())
        partfunc_dict = dict(zip(['lg(Q(1000))', 'lg(Q(500))', 'lg(Q(300))', 'lg(Q(225))',
                                    'lg(Q(150))', 'lg(Q(75))', 'lg(Q(37.5))', 'lg(Q(18.75))',
                                    'lg(Q(9.375))', 'lg(Q(5.000))', 'lg(Q(2.725))'], partfunc))
        tbl_rows.append({'tag': tag,
                            'name': molecule,
                            '#lines': nlines,
                            })
        tbl_rows[-1].update(partfunc_dict)
    tbl = Table(tbl_rows)
    return tbl


def fetch_CDMS_species():
    tbl = get_CDMS_table(CDMS_PF_filename)
    df_mol = tbl["tag", "name"].to_pandas()
    # df_mol = pd.read_csv(
    #     CDMS_PF_filename,
    #     sep='\s+', 
    #     skip_blank_lines=True,
    #     skiprows=4,
    #     usecols=[0,1],
    #     names=["tag", "name"]
    # )
    df_mol["catalog"] = "CDMS"
    return df_mol

def read_CDMS_partition_function(filename, tag):
    tbl = get_CDMS_table(filename)
    # print(tbl)

    temps = np.array([1000, 500, 300, 225, 150, 75, 37.5, 18.75, 9.375, 5.000, 2.725])
    Qvals = tbl[tbl["tag"] == tag]
    Qvals = np.array(list(Qvals[0])[3:])
    
    return temps[~np.isnan(Qvals)][::-1], 10 ** Qvals[~np.isnan(Qvals)][::-1]

def fetch_specdata(species, tag, catalog, datapath="./data/", nurange=None):

    # parittion function
    read_pf = read_CDMS_partition_function if catalog == "CDMS" else read_JPL_partition_function
    T, Q = read_pf(pf_filename[catalog], int(tag))
    if len(T) <= 3:
        func = interp1d(T, Q, fill_value="extrapolate")
        T = np.array([1000, 500, 300, 225, 150, 75, 37.5, 18.75, 9.375, 5.000, 2.725])
        Q = func(T)
        pf = PartitionFunction(species=species, T=T, Q=Q)
    else:
        pf = PartitionFunction(species=species, T=T, Q=Q)
    specdata = SpectroscopicData(filename=datapath + f"{catalog}/c{tag.zfill(6)}.cat", species=species, pf=pf, format="JPL")

    if nurange is not None:
        numin, numax = nurange
        specdata.table = specdata.table[(specdata.nu0 >= numin) & (specdata.nu0 <= numax)]
        specdata._set_quantities()
    return specdata