import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.spines.top":False,"axes.spines.right":False})
G,O,INK="#1B9E77","#D95F32","#16211D"
fig=plt.figure(figsize=(7.2,6.4)); gs=fig.add_gridspec(2,2,hspace=0.6,wspace=0.35)
ax=fig.add_subplot(gs[0,0]); x=np.arange(2); w=0.34
a=[12.0,88.0]; f=[48.5,51.5]; na=[506,3722]; nf=[65,69]
b1=ax.bar(x-w/2,a,w,color=G,label="Abstract / metadata (N = 4,228)"); b2=ax.bar(x+w/2,f,w,color=O,label="Full text, excl. reference lists (N = 134)")
for xi,v,n in zip(x-w/2,a,na): ax.text(xi,v+1.5,f"{v:.1f}%\n(n={n:,})",ha="center",fontsize=7.5)
for xi,v,n in zip(x+w/2,f,nf): ax.text(xi,v+1.5,f"{v:.1f}%\n(n={n})",ha="center",fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels(["Mentions\nsustainability","Does not\nmention"]); ax.set_ylim(0,110); ax.set_ylabel("Share of publications (%)")
ax.set_title("Sustainability language",fontsize=9.5); ax.text(-0.18,1.05,"(a)",transform=ax.transAxes,fontweight="bold",fontsize=11)
ax.yaxis.grid(True,ls="--",color="#ddd"); ax.set_axisbelow(True)
ax=fig.add_subplot(gs[0,1]); lab=["Abstract\nmentions","Full text\nmentions","Value\nflagged","Value\nconfirmed"]
v=[1.4,6.0,3.7,2.2]; n=["58/4,228","8/134","5/134","3/134"]; col=[G,O,O,O]
bars=ax.bar(range(4),v,0.6,color=col); bars[3].set_hatch("///"); bars[3].set_facecolor("white"); bars[3].set_edgecolor(O)
for i,(vv,nn) in enumerate(zip(v,n)): ax.text(i,vv+0.25,f"{vv:.1f}%\n({nn})",ha="center",fontsize=7.5)
ax.set_xticks(range(4)); ax.set_xticklabels(lab,fontsize=7.5); ax.set_ylim(0,10); ax.set_ylabel("Share of publications (%)")
ax.set_title("Green-metric reporting",fontsize=9.5); ax.text(-0.18,1.05,"(b)",transform=ax.transAxes,fontweight="bold",fontsize=11)
ax.yaxis.grid(True,ls="--",color="#ddd"); ax.set_axisbelow(True)
ax=fig.add_subplot(gs[1,0]); lab=["Mentions green\nmetrics","No improvement\nlanguage","Improvement\nlanguage (rule)"]
v=[1.4,25.9,72.7]; n=[58,1095,3075]
ax.bar(range(3),v,0.5,color=G)
for i,(vv,nn) in enumerate(zip(v,n)): ax.text(i,vv+1.5,f"{vv:.1f}%\n(n={nn:,})",ha="center",fontsize=7.5)
ax.set_xticks(range(3)); ax.set_xticklabels(lab,fontsize=7.5); ax.set_ylim(0,100); ax.set_ylabel("Share of publications (%)")
ax.set_title("Abstracts / metadata (N = 4,228)",fontsize=9.5)
ax.text(-0.18,1.05,"(c)",transform=ax.transAxes,fontweight="bold",fontsize=11); ax.yaxis.grid(True,ls="--",color="#ddd"); ax.set_axisbelow(True)
ax=fig.add_subplot(gs[1,1]); lab=["Abstract explicitly\nclaims advantage\nover batch (of 134)","Of those, full text\nreports a green-\nmetric value (of 32)"]
v=[23.9,3.1]; n=["32/134","1/32"]
bars=ax.bar(range(2),v,0.5,color=[G,O]); bars[1].set_hatch("///"); bars[1].set_facecolor("white"); bars[1].set_edgecolor(O)
for i,(vv,nn) in enumerate(zip(v,n)): ax.text(i,vv+1.5,f"{vv:.1f}%\n({nn})",ha="center",fontsize=7.5)
ax.set_xticks(range(2)); ax.set_xticklabels(lab,fontsize=7.5); ax.set_ylim(0,100); ax.set_ylabel("Share of papers (%)")
ax.set_title("Same papers, hand-labelled (N = 134)",fontsize=9.5)
ax.text(-0.18,1.05,"(d)",transform=ax.transAxes,fontweight="bold",fontsize=11); ax.yaxis.grid(True,ls="--",color="#ddd"); ax.set_axisbelow(True)
h,l=fig.axes[0].get_legend_handles_labels(); fig.legend(h,l,loc="upper center",ncol=2,frameon=False,bbox_to_anchor=(0.5,1.0),fontsize=8.5)
fig.savefig("fig3_keyword_v11.png",dpi=600,bbox_inches="tight")
