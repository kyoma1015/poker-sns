// Independent research reference: explicit cash ledger, concrete chance walk,
// occupancy moments and rank7 via21 independently scored five-card subsets.
// Does not include any existing evaluator or mutate frozen CFR data.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <vector>
static const int PLANS[5][4]={{0,0,1,1},{1,0,1,1},{1,1,1,1},{1,0,0,0},{0,0,0,0}};
static double ledger(double e,int h,int v,int actor,double pot,double rem,double fraction){
 int plans[2];plans[actor]=h;plans[1-actor]=v;double paid[2]{0,0};
 int bettor=PLANS[plans[1]][0]?1:PLANS[plans[0]][0]?0:-1;
 if(bettor<0)return e*pot-pot/2;
 int responder=1-bettor;double bet=std::min(rem,pot*fraction),raise=std::min(rem,3*bet);paid[bettor]=bet;
 auto fold=[&](int winner){return winner==actor?pot/2+paid[1-actor]:-pot/2-paid[actor];};
 if(PLANS[plans[responder]][1]&&raise>bet+1e-12){paid[responder]=raise;if(!PLANS[plans[bettor]][3])return fold(responder);paid[bettor]=raise;}
 else if(PLANS[plans[responder]][2])paid[responder]=bet;
 else return fold(bettor);
 return e*(pot+paid[0]+paid[1])-paid[actor]-pot/2;
}
extern "C" int gap_forms(int actions,int actor,double pot,double rem,double frac,double*out){
 if(actions<4||actions>5||actor<0||actor>1||!std::isfinite(pot+rem+frac)||pot<=0||rem<=0||frac<=0)return -1;
 for(int a=0;a<actions;++a)for(int b=0;b<actions;++b){int k=(a*actions+b)*2;out[k]=ledger(0,a,b,actor,pot,rem,frac);out[k+1]=ledger(1,a,b,actor,pot,rem,frac);}return 0;
}
extern "C" int gap_reference(int n,int nh,int nv,int actions,const int*holes,const int*labels,const int*hi,const int*vi,const uint16_t*w,const uint16_t*t,const double*rh,const double*rv,const double*p,const double*q,int actor,double pot,double rem,double frac,double*out,double*leaf,int*count,double*total){
 if(n<1||n>1176||nh<1||nv<1||actions<4||actions>5)return -1;
 std::vector<uint64_t>mask(n);std::vector<long double>s((nh+nv)*(actions+1)),l(169*169);std::fill(count,count+169*169,0);long double z=0;
 for(int i=0;i<n;++i){if(hi[i]<0||hi[i]>=nh||vi[i]<0||vi[i]>=nv||labels[i]<0||labels[i]>=169)return -2;mask[i]=(1ull<<holes[2*i])|(1ull<<holes[2*i+1]);}
 for(int i=0;i<n;++i)for(int j=0;j<n;++j){
  if(mask[i]&mask[j])continue;long double mass=(long double)rh[labels[i]]*rv[labels[j]];double e=(w[i*n+j]+t[i*n+j]/2.)/990.;int h=hi[i],v=vi[j],cell=labels[i]*169+labels[j];z+=mass;s[h*(actions+1)]+=mass;s[(nh+v)*(actions+1)]+=mass;long double value=0;
  for(int a=0;a<actions;++a)for(int b=0;b<actions;++b){double u=ledger(e,a,b,actor,pot,rem,frac);s[h*(actions+1)+a+1]+=mass*q[v*actions+b]*u;s[(nh+v)*(actions+1)+b+1]-=mass*p[h*actions+a]*u;value+=(long double)p[h*actions+a]*q[v*actions+b]*u;}
  l[cell]+=value;++count[cell];
 }
 if(!(z>0))return -3;*total=z;for(size_t k=0;k<s.size();++k)out[k]=s[k];for(int k=0;k<169*169;++k)leaf[k]=count[k]?l[k]/count[k]:0;return 0;
}
extern "C" int gap_board_chance(int n,const int*holes,const int*labels,const double*rh,const double*rv,double*out,double*total){
 if(n!=1326)return -1;std::vector<uint64_t>mask(n);std::array<long double,52>one{};std::vector<long double>two(52*52),three(52*52*52);long double z=0;
 for(int i=0;i<n;++i)mask[i]=(1ull<<holes[2*i])|(1ull<<holes[2*i+1]);
 for(int i=0;i<n;++i)for(int j=0;j<n;++j){if(mask[i]&mask[j])continue;long double m=(long double)rh[labels[i]]*rv[labels[j]];if(!std::isfinite((double)m)||m<0)return -2;int c[4]{holes[2*i],holes[2*i+1],holes[2*j],holes[2*j+1]};std::sort(c,c+4);z+=m;for(int a=0;a<4;++a)one[c[a]]+=m;for(int a=0;a<4;++a)for(int b=a+1;b<4;++b)two[c[a]*52+c[b]]+=m;for(int a=0;a<4;++a)for(int b=a+1;b<4;++b)for(int d=b+1;d<4;++d)three[(c[a]*52+c[b])*52+c[d]]+=m;}
 if(!(z>0))return -3;int k=0;for(int a=0;a<50;++a)for(int b=a+1;b<51;++b)for(int c=b+1;c<52;++c){long double m=z-one[a]-one[b]-one[c]+two[a*52+b]+two[a*52+c]+two[b*52+c]-three[(a*52+b)*52+c];if(m<-1e-12L*z)return -4;out[k++]=std::max(0.L,m)/(z*17296.L);}*total=z;return 0;
}
extern "C" int gap_direct_mass(int n,const int*holes,const int*labels,const double*rh,const double*rv,const int*flop,double*out){
 uint64_t board=(1ull<<flop[0])|(1ull<<flop[1])|(1ull<<flop[2]);long double z=0;std::vector<uint64_t>mask(n);for(int i=0;i<n;++i)mask[i]=(1ull<<holes[2*i])|(1ull<<holes[2*i+1]);for(int i=0;i<n;++i)if(!(mask[i]&board))for(int j=0;j<n;++j)if(!(mask[j]&(board|mask[i])))z+=(long double)rh[labels[i]]*rv[labels[j]];*out=z;return 0;
}
static uint64_t rank5(const std::array<int,5>&c){
 int counts[15]{};std::vector<int>r;bool flush=true;for(int x:c){++counts[x/4+2];flush&=x%4==c[0]%4;}for(int i=14;i>=2;--i)if(counts[i])r.push_back(i);int straight=0;if(r.size()==5){if(r[0]-r[4]==4)straight=r[0];if(r==std::vector<int>{14,5,4,3,2})straight=5;}
 std::vector<std::pair<int,int>>groups;for(int v:r)groups.push_back({counts[v],v});std::sort(groups.rbegin(),groups.rend());int category=0;std::vector<int>digits;
 if(flush&&straight){category=8;digits={straight};}
 else if(groups[0].first==4){category=7;digits={groups[0].second,groups[1].second};}
 else if(groups[0].first==3&&groups[1].first==2){category=6;digits={groups[0].second,groups[1].second};}
 else if(flush){category=5;digits=r;}
 else if(straight){category=4;digits={straight};}
 else {category=groups[0].first==3?3:groups[0].first==2&&groups[1].first==2?2:groups[0].first==2?1:0;for(auto g:groups)digits.push_back(g.second);}
 uint64_t score=category;for(int i=0;i<5;++i)score=score*15+(i<(int)digits.size()?digits[i]:0);return score;
}
static uint64_t rank7(const int*c){uint64_t best=0;for(int a=0;a<3;++a)for(int b=a+1;b<4;++b)for(int d=b+1;d<5;++d)for(int e=d+1;e<6;++e)for(int f=e+1;f<7;++f)best=std::max(best,rank5({c[a],c[b],c[d],c[e],c[f]}));return best;}
extern "C" uint64_t gap_rank7(const int*c){return rank7(c);}
extern "C" int gap_exact_reference(const int*holes,const int*flop,uint64_t*out){
 bool used[52]{};for(int i=0;i<7;++i){int c=i<4?holes[i]:flop[i-4];if(c<0||c>=52||used[c])return -1;used[c]=true;}std::vector<int>deck;for(int c=0;c<52;++c)if(!used[c])deck.push_back(c);std::fill(out,out+3,0);int h[7]{holes[0],holes[1],flop[0],flop[1],flop[2]},v[7]{holes[2],holes[3],flop[0],flop[1],flop[2]};for(int a=0;a<44;++a)for(int b=a+1;b<45;++b){h[5]=v[5]=deck[a];h[6]=v[6]=deck[b];auto x=rank7(h),y=rank7(v);++out[x>y?0:x==y?1:2];}return 0;
}
extern "C" int gap_solve(int nh,int nv,int actions,const double*a,const double*prior,int iterations,double*average,double*regrets){
 if(nh<1||nv<1||actions<4||actions>5||iterations<1)return -1;int hp=nh*actions,vp=nv*actions;std::vector<double>rh(hp),rv(vp),p(hp),q(vp),avg(hp+vp);
 for(int i=0;i<nh*nv*actions*actions;++i)if(!std::isfinite(a[i]))return -2;for(int k=0;k<nh+nv;++k){double z=0;for(int x=0;x<actions;++x){double v=prior[k*actions+x];if(!std::isfinite(v)||v<0)return -3;z+=v;}if(std::abs(z-1)>1e-10)return -3;}
 auto match=[&](const std::vector<double>&r,std::vector<double>&x){for(int k=0;k<(int)x.size()/actions;++k){double z=0;for(int b=0;b<actions;++b){x[k*actions+b]=std::max(0.,r[k*actions+b]);z+=x[k*actions+b];}for(int b=0;b<actions;++b)x[k*actions+b]=z?x[k*actions+b]/z:1./actions;}};
 for(int t=0;t<iterations;++t){if(t==0){std::copy(prior,prior+hp,p.begin());std::copy(prior+hp,prior+hp+vp,q.begin());}else{match(rh,p);match(rv,q);}std::vector<double>h(hp),v(vp);for(int i=0;i<nh;++i)for(int j=0;j<nv;++j)for(int x=0;x<actions;++x)for(int y=0;y<actions;++y){double u=a[((i*nv+j)*actions+x)*actions+y];h[i*actions+x]+=u*q[j*actions+y];v[j*actions+y]-=u*p[i*actions+x];}for(int i=0;i<nh;++i){double u=0;for(int x=0;x<actions;++x)u+=p[i*actions+x]*h[i*actions+x];for(int x=0;x<actions;++x){rh[i*actions+x]+=h[i*actions+x]-u;avg[i*actions+x]+=p[i*actions+x];}}for(int j=0;j<nv;++j){double u=0;for(int x=0;x<actions;++x)u+=q[j*actions+x]*v[j*actions+x];for(int x=0;x<actions;++x){rv[j*actions+x]+=v[j*actions+x]-u;avg[hp+j*actions+x]+=q[j*actions+x];}}}for(int i=0;i<hp+vp;++i){average[i]=avg[i]/iterations;regrets[i]=i<hp?rh[i]:rv[i-hp];}return 0;
}
