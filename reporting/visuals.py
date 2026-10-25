"""Presentation-only figures drawn from retained numerical evidence."""
from pathlib import Path
import csv


def supporting_figures(bins, importance, destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.ticker import PercentFormatter
    destination=Path(destination)
    fig,axes=plt.subplots(1,2,figsize=(8.8,3.7))
    for ax,variant,limit in zip(axes,('As fitted','Fold-prior corrected'),(1.,.30)):
        part=[r for r in bins if r['variant']==variant]
        x=[float(r['mean_predicted']) for r in part];y=[float(r['observed_rate']) for r in part]
        if max(x+y)>limit:raise ValueError('Calibration axes would omit a saved point')
        ax.plot([0,limit],[0,limit],ls='--',color='#68727b',lw=1)
        ax.plot(x,y,color='#21678d',lw=1)
        ax.scatter(x,y,s=[float(r['count'])*.35 for r in part],color='#21678d',zorder=3)
        ax.set(xlim=(0,limit),ylim=(0,limit),xlabel='Mean predicted hazard probability',ylabel='Observed hazardous fraction')
        ax.set_title(variant+'\n'+str(len(part))+' nonempty bins; n='+str(sum(int(r['count']) for r in part)),fontsize=13)
        ax.xaxis.label.set_size(12);ax.yaxis.label.set_size(12)
        ticks=np.linspace(0,limit,4 if limit<1 else 6)
        ax.set_xticks(ticks);ax.set_yticks(ticks)
        ax.xaxis.set_major_formatter(PercentFormatter(1,decimals=0));ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
        ax.tick_params(labelsize=12);ax.grid(alpha=.15);ax.spines[['top','right']].set_visible(False)
    fig.tight_layout(w_pad=2)
    fig.savefig(destination/'calibration_detail.png',dpi=320,bbox_inches='tight')
    fig.savefig(destination/'calibration_detail.svg',bbox_inches='tight');plt.close(fig)
    globally=sorted([r for r in importance if r['validation']=='time' and int(r['fold'])==-1],key=lambda r:-float(r['mean_abs']))[:8]
    shares=[]
    for r in globally:
        row=[]
        for fold in range(4):
            part=[v for v in importance if v['validation']=='time' and int(v['fold'])==fold]
            row.append(float(next(v['mean_abs'] for v in part if v['feature']==r['feature']))/sum(float(v['mean_abs']) for v in part))
        shares.append(row)
    fig,(left,right)=plt.subplots(1,2,figsize=(9.2,4.5),gridspec_kw={'width_ratios':[1.15,1]},sharey=True)
    left.barh(range(8),[float(r['mean_abs']) for r in globally],color='#21678d')
    left.set_yticks(range(8),[r['feature'] for r in globally]);left.invert_yaxis()
    left.set_xlabel('Mean absolute SHAP contribution\n(raw log-odds)',fontsize=13)
    left.set_title('Common-cohort feature use',fontsize=14);left.grid(axis='x',alpha=.15)
    left.spines[['top','right']].set_visible(False);left.tick_params(labelsize=13)
    # Draw the 32 heatmap cells as vector quadrilaterals, not an embedded bitmap.
    matrix=np.asarray(shares)
    right.pcolormesh(np.arange(5)-.5,np.arange(9)-.5,matrix,cmap='Blues',vmin=0,
                    vmax=max(.3,float(matrix.max())),shading='flat')
    right.set_xlim(-.5,3.5);right.set_ylim(7.5,-.5)
    right.set_xticks(range(4),['Block 1','Block 2','Block 3','Block 4']);right.tick_params(axis='y',left=False,labelleft=False)
    right.set_title('Share of all 17 contributions',fontsize=13)
    right.tick_params(axis='x',labelsize=12)
    for i,row in enumerate(shares):
        for j,value in enumerate(row):right.text(j,i,f'{100*value:.1f}%',ha='center',va='center',fontsize=13,color='white' if value>.18 else '#152635')
    fig.tight_layout(w_pad=1)
    fig.savefig(destination/'shap_readable.png',dpi=320,bbox_inches='tight')
    fig.savefig(destination/'shap_readable.svg',bbox_inches='tight');plt.close(fig)


def monitoring_figure(evaluations, intervals, destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    destination=Path(destination);rows=[]
    for fold in (0,1,2,3,-1):
        for budget in (.01,.05,.1,.2):
            e=next(r for r in evaluations if int(r['fold'])==fold and float(r['budget'])==budget)
            ci=next(r for r in intervals if int(r['fold'])==fold and float(r['budget'])==budget and int(r['block_length'])==32)
            rows.append({**{k:e[k] for k in ('fold','budget','n','positives','k','base_etp','extended_etp','delta_etp')},
                         **{k:ci[k] for k in ('block_length','ci_low','ci_high')}})
    with (destination/'monitoring_increment.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    fig,axes=plt.subplots(5,1,figsize=(8.5,7.1),sharex=True)
    for ax,fold in zip(axes,(0,1,2,3,-1)):
        part=[r for r in rows if int(r['fold'])==fold]
        for y,r in enumerate(part):
            ax.plot([float(r['ci_low']),float(r['ci_high'])],[y,y],color='#21678d',lw=1.8)
            ax.plot(float(r['delta_etp']),y,'o',color='#21678d',ms=4)
        title='Pooled (supplementary)' if fold<0 else f'Record block {fold+1}'
        ax.text(1.02,.5,title+'\nn='+str(part[0]['n'])+', P='+str(part[0]['positives']),transform=ax.transAxes,va='center',fontsize=12)
        ax.set_yticks(range(4),['1%','5%','10%','20%']);ax.set_ylim(3.55,-.55)
        ax.set_ylabel('Batch slots',fontsize=12);ax.axvline(0,ls='--',color='#68727b',lw=.8)
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.15);ax.tick_params(labelsize=12)
        if fold<0:ax.set_facecolor('#eef2f5')
    axes[-1].set_xlabel('Extended minus base expected detections\n(positive favors monitoring)',fontsize=13)
    fig.tight_layout(h_pad=.65,rect=(0,0,.82,1))
    fig.savefig(destination/'monitoring_increment.png',dpi=320,bbox_inches='tight')
    fig.savefig(destination/'monitoring_increment.svg',bbox_inches='tight');plt.close(fig)


def add_svg_alternative(inline, path, part):
    """Word's SVG extension retains an editable vector source plus PNG fallback."""
    from docx.opc.part import Part
    from docx.opc.packuri import PackURI
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    from docx.oxml import OxmlElement
    from lxml import etree
    package=part.package
    name=package.next_partname('/word/media/vector%d.svg')
    image_part=Part(PackURI(str(name)),'image/svg+xml',Path(path).read_bytes(),package)
    rid=part.relate_to(image_part,RT.IMAGE)
    blip=inline._inline.xpath('.//a:blip')[0]
    ext_list=OxmlElement('a:extLst');ext=OxmlElement('a:ext')
    ext.set('uri','{96DAC541-7B7A-43D3-8B79-37D633B846F1}')
    node=etree.Element('{http://schemas.microsoft.com/office/drawing/2016/SVG/main}svgBlip',nsmap={'asvg':'http://schemas.microsoft.com/office/drawing/2016/SVG/main'})
    node.set('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed',rid)
    ext.append(node);ext_list.append(ext);blip.append(ext_list)
