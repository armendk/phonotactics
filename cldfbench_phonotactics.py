import re
import pathlib
import collections

import pycountry
from clldutils.misc import slug
from cldfbench import Dataset as BaseDataset
from cldfbench import CLDFSpec
from csvw import TableGroup

URL = "https://zenodo.org/record/815506/files/phonotactics.csv"
# Columns we consider language metadata, rather than proper parameters:
LDATA = collections.OrderedDict([
    ('ID', ('ID', None)),
    ('Language', ('Name', None)),
    ('ISO code', ('ISO639P3code', None)),
    ('Latitude', ('Latitude', None)),
    ('Longitude', ('Longitude', None)),
    ('Language family', 'Lineage_0'),
    ('Language family:1', 'Lineage_1'),
    ('Language family:2', 'Lineage_2'),
    ('Language family:3', 'Lineage_3'),
    ('Language family:4', 'Lineage_4'),
    ('Language family:5', 'Lineage_5'),
    ("Is this language an isolate?", ('Isolate', 'boolean')),
    ("World macro-region", ('Macroarea', None)),
    ("WALS area", 'WALS_Area'),
    ("Autotyp", 'Autotyp'),
    ("Country", 'Country'),  # ISO 3166-1 alpha-2
    ("Ancient language", ('Ancient', 'boolean')),
    ("Papuan", ('Papuan', 'boolean')),
    ("Altitude", ('Altitude', 'number')),  # in meters
    ("Eastness", ('Eastness', 'number')),
    ("Ethnologue Ethnic Population", ('Ethnologue_Ethnic_Population', 'integer')),
    ("Adjusted population", ('Adjusted_Population', 'integer')),
    ("Social Region", 'Social_Region'),
])


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "phonotactics"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(module='StructureDataset', dir=self.cldf_dir)

    def cmd_readme(self, args):
        lines, title_found = [], False
        for line in super().cmd_readme(args).split('\n'):
            lines.append(line)
            if line.startswith('# ') and not title_found:
                title_found = True
                lines.extend([
                    '',
                    "[![Build Status](https://travis-ci.org/cldf-datasets/phonotactics.svg?branch=master)]"
                    "(https://travis-ci.org/cldf-datasets/phonotactics)"
                ])
        lines.extend(['', self.dir.joinpath('NOTES.md').read_text(encoding='utf8')])
        return '\n'.join(lines)

    def cmd_download(self, args):
        self.raw_dir.download(URL + '?download=1', 'phonotactics.csv')
        self.raw_dir.download(URL + '-metadata.json?download=1', 'metadata.json')

    def cmd_makecldf(self, args):
        def parameter_id(s):
            return slug(s, lowercase=False)

        lcols = []
        for spec in LDATA.values():
            if isinstance(spec, tuple):
                col, dtype = spec
            else:
                col, dtype = spec, 'string'
            if dtype:
                lcols.append(dict(name=col, datatype=dtype))
        args.writer.cldf.add_component('LanguageTable', *lcols)
        args.writer.cldf.add_component(
            'ParameterTable',
            {'name': 'datatype', 'datatype': {'base': 'string', 'format': 'boolean|number|integer'}},
            'min',
            'max')
        args.writer.cldf.remove_columns('ValueTable', 'Comment', 'Source')

        iso2gc = {l.iso: l.id for l in args.glottolog.api.languoids() if l.iso}
        dt_map = {
            r['Parameter_ID']: r['datatype']
            for r in self.etc_dir.read_csv('parameters.csv', dicts=True)}

        tg = TableGroup.from_file(self.raw_dir / 'metadata.json')
        colmap = {}
        seen = set()
        for col in tg.tables[0].tableSchema.columns:
            if col.header not in LDATA:
                pid = parameter_id(col.header)
                if pid not in seen:
                    col.datatype.base = dt_map.get(pid, col.datatype.base)
                    colmap[pid] = col.datatype
                    kw = {
                        'ID': pid,
                        'Name': col.header,
                        'Description': col.common_props['dc:description'].strip() or None,
                        'datatype': col.datatype.base,
                    }
                    if col.datatype.minimum is not None:
                        kw['min'] = col.datatype.minimum
                        kw['max'] = col.datatype.maximum
                    args.writer.objects['ParameterTable'].append(kw)
                    seen.add(pid)

        gc_map = {
            r['ID']: r['Glottocode'] for r in self.etc_dir.read_csv('languages.csv', dicts=True)}
        country_map = {
            r['country']: r['alpha_2'] for r in self.etc_dir.read_csv('countries.csv', dicts=True)}
        vals = {}
        for i, row in enumerate(tg.tables[0]):
            lid = row['ID']
            m = re.search('(?P<code>[a-z]{3})(-[0-9]+)?', row['ISO code'] or '')
            row['ISO code'] = m.group('code') if m else None
            kw = {'Glottocode': gc_map.get(row['ID'], iso2gc.get(row['ISO code']))}
            for k, v in LDATA.items():
                kw[v[0] if isinstance(v, tuple) else v] = row.pop(k)
            kw['Macroarea'] = 'Papunesia' if kw['Macroarea'] == 'Pacific' else kw['Macroarea']
            if kw['Country']:
                if kw['Country'] in country_map:
                    kw['Country'] = country_map[kw['Country']] or None
                else:
                    kw['Country'] = pycountry.countries.lookup(kw['Country']).alpha_2
            args.writer.objects['LanguageTable'].append(kw)

            for col, val in row.items():
                if val is None:
                    continue
                pid = parameter_id(col)
                dtype = colmap[pid]
                if dtype.base in ('integer', 'number'):
                    assert dtype.minimum <= val <= dtype.maximum
                elif dtype.base == 'boolean':
                    val = {True: 'yes', False: 'no'}[val]
                if (lid, pid) in vals:
                    assert vals[lid, pid] == val
                    continue
                vals[lid, pid] = val
                if col not in LDATA:
                    args.writer.objects['ValueTable'].append({
                        'ID': '{0}-{1}'.format(kw['ID'], pid),
                        'Language_ID': kw['ID'],
                        'Parameter_ID': pid,
                        'Value': val,
                    })
