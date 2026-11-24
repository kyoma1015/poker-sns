// Sparse external-sampling CFR on the original native game. Research only.
#include "g11_native_state.h"
#include "fullstreet_core.cc"
#include <pybind11/numpy.h>
#include <unordered_map>
#include <fstream>
#include <sstream>
#include <random>
#include <chrono>
#include <set>
using namespace pybind11::literals;
namespace pn=pokerid11state;
using I=pn::I;using V=pn::V;using H=std::vector<std::array<I,5>>;
static std::string history_key(int round,const H&hist){std::string out;out.push_back(char(round));for(auto h:hist){out.push_back(char(h[0]));out.push_back(char(h[1]));int16_t a=h[2];out.append((char*)&a,2);}return out;}
static uint64_t visible_rank(const V&own,const V&board,int n){V cs=own;cs.insert(cs.end(),board.begin(),board.begin()+n);if(cs.size()==7){int a[7];std::copy(cs.begin(),cs.end(),a);return fast(a);}pn::V best;
 if(cs.size()==5)best=pn::five(cs);else for(int x=0;x<6;++x){V five;for(int j=0;j<6;++j)if(j!=x)five.push_back(cs[j]);best=std::max(best,pn::five(five));}
 std::array<int,6>r{};for(size_t j=0;j<best.size();++j)r[j]=best[j];return encode(r);}
static int texture_bits(const V&own,const V&board,int n){int ranks[15]{},suits[4]{},bs[4]{};unsigned mask=0;for(I c:own){ranks[c/4+2]++;suits[c%4]++;mask|=1u<<(c/4+2);}for(int j=0;j<n;++j){I c=board[j];ranks[c/4+2]++;suits[c%4]++;bs[c%4]++;mask|=1u<<(c/4+2);}int draw=*std::max_element(suits,suits+4)>=4,connect=0;for(int hi=5;hi<=14;++hi){unsigned bits=hi==5?0x403c:(31u<<(hi-4));if(__builtin_popcount(mask&bits)>=4)connect=1;}int pairs=0;std::set<int>r;for(int j=0;j<n;++j)r.insert(board[j]/4);pairs=n-r.size();return draw+2*connect+4*std::min(3,pairs)+16*(*std::max_element(bs,bs+4));}
// Compact own/public signals. Global suit permutations leave this unchanged.
// Earlier streets retain made-hand categories, current street adds texture/draw/
// relative strength and nut-flush blockers; this is an imperfect-recall abstraction.
static uint32_t shared_signal(const V&own,const V&board){
 int n=board.size(),cat=visible_rank(own,board,n)/759375,primary=(visible_rank(own,board,n)/50625)%15;
 int high=0,second=0,bs[4]{};unsigned ranks=0;std::set<int>unique;
 for(I c:board){int r=c/4+2;unique.insert(r);ranks|=1u<<r;bs[c%4]++;if(r>high){second=high;high=r;}else second=std::max(second,r);}
 int relative=primary>=high?2:primary>=second?1:0,major=*std::max_element(bs,bs+4),block=0,connected=0;
 for(I c:own)if(c/4==12&&bs[c%4]>=2)block=1;
 for(int hi=5;hi<=14;++hi){unsigned bits=hi==5?0x403c:(31u<<(hi-4));connected|=__builtin_popcount(ranks&bits)>=4;}
 int draw=texture_bits(own,board,n)&3;
 int flush_hole=0;for(I c:own)if(bs[c%4]==major&&major>=3)flush_hole=std::max(flush_hole,int(c/4+2));
 int base=cat+9*(relative+3*(draw+4*((unique.size()<size_t(n))+2*((major>=3)+2*(connected+2*block)))));
 int secondary=(cat==2||cat==6)?int((visible_rank(own,board,n)/3375)%15):0;
 return base+1728*(primary+15*(flush_hole+15*secondary));
}
static double equity_prefix(const V&,const V&,int,uint64_t);
struct Warm{int base,round;V actions;std::vector<double>R,A;};
struct Row{V actions;std::vector<double>R,A,prior;uint64_t visits=0,averages=0;bool warm=false;};
struct Pending{std::vector<double>R,A;uint64_t visits=0,averages=0;};
struct NeedAction:std::exception{};
class Sparse {
 std::shared_ptr<pn::Spec>spec;std::unordered_map<std::string,Row>rows;std::unordered_map<std::string,Warm>warm;std::vector<double>oldpi,pre_equity;std::vector<uint8_t>old_support;std::vector<int>classes;std::mt19937_64 master;bool full,refined,sharing=false;std::unordered_map<std::string,V>extra;size_t maxrows,nodecap;std::unordered_map<Row*,Pending>pending;uint64_t nodes=0,iterations=0,allocated=0;double deadline=0;bool scripted=false;V script;size_t script_at=0;std::vector<double>need;std::chrono::steady_clock::time_point begin;
 double seconds(){return std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();}
 int hand(const V&own)const{return classes[own[0]*52+own[1]];}
 std::string key(const V&own,const V&board,int p,int round,const H&hist)const{std::string k=history_key(round,hist);k.push_back(char(p));
  if(sharing&&round>0){int hi=std::max(own[0]/4+2,own[1]/4+2),lo=std::min(own[0]/4+2,own[1]/4+2);bool relevant=lo>=10;uint64_t made=visible_rank(own,board,board.size());for(int div=50625;div>=1;div/=15)relevant=relevant||int((made/div)%15)==lo;k.push_back(char(hi));k.push_back(char(relevant?lo:0));k.push_back(char((hi==lo)+2*(own[0]%4==own[1]%4)));for(int n:{3,4,5})if(board.size()>size_t(n))k.push_back(char(visible_rank(own,board,n)/759375));uint32_t f=shared_signal(own,board);k.append((char*)&f,4);return k;}
  int16_t h=hand(own);k.append((char*)&h,2);int o[2]{int(own[0]),int(own[1])},b[5]{};for(size_t j=0;j<board.size();++j)b[j]=board[j];
  for(int n:{3,4,5})if(board.size()>=size_t(n)){int old=n==5?fs_nuts(o,b):fs_feature(o,b,n);k.push_back(char(old));std::set<int>rs;for(int j=0;j<n;++j)rs.insert(board[j]/4);k.push_back(char(rs.size()<size_t(n)));if(refined){uint64_t v=visible_rank(own,board,n);k.append((char*)&v,8);uint16_t t=texture_bits(own,board,n);k.append((char*)&t,2);}}
  return k;}
 static std::vector<double>matching(const Row&r,bool average){const auto&v=average?r.A:r.R;double z=std::accumulate(v.begin(),v.end(),0.);if(z<=0)return r.prior;std::vector<double>p(v.size());for(size_t a=0;a<v.size();++a)p[a]=v[a]/z;return p;}
 V selected(const V&legal,int p,const V&live,const V&street,const V&remaining,I price,const Warm*w)const{if(full)return legal;std::set<I>a;for(I x:legal)if(x<=1)a.insert(x);V raises;for(I x:legal)if(x>1)raises.push_back(x);if(!raises.empty()){a.insert(raises.front());a.insert(raises.back());I cost=std::min(remaining[p],std::max(I(0),price-street[p]));double pot=std::accumulate(live.begin(),live.end(),I(0))+cost;for(double f:{.5,.75,1.,1.25,1.5,2.}){I target=std::llround(price+f*pot)+2;auto it=std::min_element(raises.begin(),raises.end(),[&](I x,I y){return std::abs(x-target)<std::abs(y-target);});a.insert(*it);}}if(w)for(I x:w->actions)if(std::find(legal.begin(),legal.end(),x)!=legal.end())a.insert(x);return V(a.begin(),a.end());}
 Row initial(const V&own,const V&board,int p,int round,const H&hist,const V&legal,const V&live,const V&street,const V&remaining,I price)const{
  const Warm*w=nullptr;auto found=warm.find(history_key(round,hist));if(found!=warm.end())w=&found->second;Row row;row.actions=selected(legal,p,live,street,remaining,price,w);
  auto extras=extra.find(history_key(round,hist));if(extras!=extra.end()){for(I a:extras->second)if(std::find(legal.begin(),legal.end(),a)!=legal.end())row.actions.push_back(a);std::sort(row.actions.begin(),row.actions.end());row.actions.erase(std::unique(row.actions.begin(),row.actions.end()),row.actions.end());}
  size_t n=row.actions.size();row.R.assign(n,0.);row.A.assign(n,0.);row.prior.assign(n,0.);
  double eq=pre_equity[hand(own)];if(round>0){if(refined){uint64_t r=visible_rank(own,board,board.size());int cat=r/759375;eq=std::min(.98,.2+.105*cat+.012*(int((r/50625)%15)));if(texture_bits(own,board,board.size())&1)eq=std::min(.98,eq+.08);}else{int o[2]{int(own[0]),int(own[1])},b[5]{};for(size_t j=0;j<board.size();++j)b[j]=board[j];int flag=round==3?fs_nuts(o,b):fs_feature(o,b,round==1?3:4);eq=round==3&&flag?.99:std::clamp(.35*eq+(flag?.4:.2),.05,.95);}}
  double cost=std::min(remaining[p],std::max(I(0),price-street[p]));double pot=std::accumulate(live.begin(),live.end(),I(0));double odds=cost/(pot+cost+1e-12);double raise=.02+.32*std::max(0.,(eq-.55)/.45),call=cost>0?std::clamp(.1+1.6*(eq-odds),.08,.93-raise):.98-raise;double fold=std::max(.001,1-call-raise),rz=0.;
  for(I a:row.actions)if(a>1)rz+=1./std::max(1.,double(a-2-price));for(size_t a=0;a<n;++a){I x=row.actions[a];row.prior[a]=x==0?fold:x==1?call:raise/(rz*std::max(1.,double(x-2-price)));}
  double z=std::accumulate(row.prior.begin(),row.prior.end(),0.);for(auto&x:row.prior)x/=z;
  if(w){int o[2]{int(own[0]),int(own[1])},b[5]{};for(size_t j=0;j<board.size();++j)b[j]=board[j];int code=8*hand(own);if(round>=1)code+=4*fs_feature(o,b,3);if(round>=2)code+=2*fs_feature(o,b,4);if(round==3)code+=fs_nuts(o,b);int pub=0;for(int nn:{3,4,5})if(board.size()>=size_t(nn)){std::set<int>r;for(int j=0;j<nn;++j)r.insert(board[j]/4);pub+=(r.size()<size_t(nn))<<(5-nn);}int at=w->base+((pub>>(3-round))*(169<<round)+(code>>(3-round)))*w->actions.size();
   for(size_t a=0;a<n;++a){auto it=std::find(w->actions.begin(),w->actions.end(),row.actions[a]);if(it!=w->actions.end()){int j=it-w->actions.begin();row.prior[a]=.98*oldpi[at+j]+.02*row.prior[a];row.warm=row.warm||old_support[at+j];if(round==0&&!w->R.empty()){row.R[a]=w->R[hand(own)*w->actions.size()+j];row.A[a]=w->A[hand(own)*w->actions.size()+j];}}else row.prior[a]*=.02;}
   z=std::accumulate(row.prior.begin(),row.prior.end(),0.);for(auto&x:row.prior)x/=z;
  }
  for(size_t a=0;a<n;++a){row.R[a]=std::max(row.R[a],1e-6*row.prior[a]);row.A[a]+=1e-3*row.prior[a];}return row;
 }
 Row& get(const pn::State&s){const auto&e=s.engine;auto k=key(s.holes[e.actor],s.board,e.actor,e.round,e.history);auto it=rows.find(k);if(it!=rows.end())return it->second;if(rows.size()>=maxrows)throw std::runtime_error("row budget; incomplete pair discarded");auto r=initial(s.holes[e.actor],s.board,e.actor,e.round,e.history,s.legal_actions(),e.live,e.street,e.remaining,e.price);size_t bytes=sizeof(Row)+k.size()+128+32*r.actions.size();if(allocated+bytes>128ULL*1024*1024)throw std::runtime_error("128MiB sparse row budget; incomplete pair discarded");allocated+=bytes;return rows.emplace(std::move(k),std::move(r)).first->second;}
 Pending& update(Row&r){auto it=pending.find(&r);if(it!=pending.end())return it->second;Pending p;p.R.assign(r.actions.size(),0.);p.A=p.R;return pending.emplace(&r,std::move(p)).first->second;}
 static void fill(pn::State&s,const V&world){while(s.chance()&&!s.terminal())s.apply(world[4+s.board.size()]);}
 static double value(const pn::State&s){auto&e=s.engine;if(e.folded[0])return -e.live[0]/2.;if(e.folded[1])return e.live[1]/2.;int a[7],b[7];for(int j=0;j<2;++j){a[j]=s.holes[0][j];b[j]=s.holes[1][j];}for(int j=0;j<5;++j)a[2+j]=b[2+j]=s.board[j];auto x=fast(a),y=fast(b);return (x>y?1.:x<y?-1.:0.)*std::min(e.live[0],e.live[1])/2.;}
 double walk(pn::State s,int owner,const V&world,std::mt19937_64&rng){if(++nodes>nodecap||(nodes%256==0&&seconds()>deadline))throw std::runtime_error("node/time budget; incomplete pair discarded");fill(s,world);if(s.terminal())return(owner==0?1:-1)*value(s);int p=s.engine.actor;Row&row=get(s);auto pi=matching(row,false);Pending&u=update(row);
  if(p!=owner){u.averages++;for(size_t a=0;a<pi.size();++a)u.A[a]+=(iterations+1)*pi[a];int a;if(scripted){if(script_at==script.size()){need=pi;throw NeedAction();}a=script[script_at++];if(a<0||size_t(a)>=pi.size())throw std::invalid_argument("scripted action index");}else{std::discrete_distribution<int>d(pi.begin(),pi.end());a=d(rng);}s.apply(row.actions[a]);return walk(s,owner,world,rng);}
  std::vector<double>v(pi.size());double z=0.;for(size_t a=0;a<pi.size();++a){pn::State c=s;c.apply(row.actions[a]);v[a]=walk(std::move(c),owner,world,rng);z+=pi[a]*v[a];}u.visits++;for(size_t a=0;a<pi.size();++a)u.R[a]+=v[a]-z;return z;
 }
public:
 Sparse(py::object game,py::dict data,uint64_t seed,bool all,bool fine,size_t limit,size_t budget):spec(std::make_shared<pn::Spec>(game)),master(seed),full(all),refined(fine),maxrows(limit),nodecap(budget){
  if(data.contains("sharing"))sharing=data["sharing"].cast<bool>();
  if(data.contains("extra_support"))for(auto x:data["extra_support"].cast<py::list>()){auto d=x.cast<py::dict>();extra.emplace(history_key(d["round"].cast<int>(),d["history"].cast<H>()),d["actions"].cast<V>());}
  pn::State s(spec);if(s.engine.n!=2||s.engine.bb!=2)throw std::invalid_argument("explicit HU bb2 required");if(s.engine.bba||s.engine.num)throw std::invalid_argument("zero ante/rake only");classes=data["classes"].cast<std::vector<int>>();if(classes.size()!=2704)throw std::invalid_argument("card class map");auto pa=data["pi"].cast<py::array_t<double,py::array::c_style>>();oldpi.assign(pa.data(),pa.data()+pa.size());auto sa=data["support"].cast<py::array_t<uint8_t,py::array::c_style>>();old_support.assign(sa.data(),sa.data()+sa.size());pre_equity=data["equity"].cast<std::vector<double>>();if(old_support.size()!=oldpi.size()||pre_equity.size()!=169)throw std::invalid_argument("warm shape");
  for(auto x:data["nodes"].cast<py::list>()){auto d=x.cast<py::dict>();Warm w;w.base=d["base"].cast<int>();w.round=d["round"].cast<int>();w.actions=d["actions"].cast<V>();w.R=d["R"].cast<std::vector<double>>();w.A=d["A"].cast<std::vector<double>>();warm.emplace(history_key(w.round,d["history"].cast<H>()),std::move(w));}
 }
 void seed_preflop(py::list data){if(iterations||!rows.empty())throw std::runtime_error("bootstrap before training only");for(auto item:data){auto d=item.cast<py::dict>();std::string k=d["key"].cast<std::string>();if(k.empty()||k[0]!=0)throw std::invalid_argument("preflop finitewarm only");Row r;r.actions=d["actions"].cast<V>();r.R=d["R"].cast<std::vector<double>>();r.A=d["A"].cast<std::vector<double>>();r.prior=d["prior"].cast<std::vector<double>>();size_t n=r.actions.size();if(!n||r.R.size()!=n||r.A.size()!=n||r.prior.size()!=n)throw std::invalid_argument("bootstrap shape");for(size_t j=0;j<n;++j)if(r.R[j]<0||r.A[j]<0||r.prior[j]<0||!std::isfinite(r.R[j]+r.A[j]+r.prior[j]))throw std::invalid_argument("bootstrap values");r.warm=true;allocated+=sizeof(Row)+k.size()+128+32*n;rows.emplace(k,std::move(r));}}
 py::dict step(double seconds_budget){begin=std::chrono::steady_clock::now();deadline=seconds_budget;nodes=0;pending.clear();scripted=false;V cards(52);std::iota(cards.begin(),cards.end(),0);std::shuffle(cards.begin(),cards.end(),master);V world(cards.begin(),cards.begin()+9);uint64_t seeds[2]{master(),master()};bool complete=false;std::string error;
  try{for(int p=0;p<2;++p){pn::State s(spec);for(int j=0;j<4;++j)s.apply(world[j]);std::mt19937_64 rng(seeds[p]);walk(std::move(s),p,world,rng);}for(auto&[r,u]:pending){for(size_t a=0;a<r->R.size();++a){r->R[a]=std::max(0.,r->R[a]+u.R[a]);r->A[a]+=u.A[a];}r->visits+=u.visits;r->averages+=u.averages;}++iterations;complete=true;}catch(const std::runtime_error&e){error=e.what();}pending.clear();return py::dict("complete"_a=complete,"error"_a=error,"nodes"_a=nodes,"iterations"_a=iterations,"rows"_a=rows.size());
 }
 py::dict query(const V&own,const V&board,int p,int round,const H&hist,const V&legal,const V&live,const V&street,const V&remaining,I price,bool average){auto k=key(own,board,p,round,hist);auto it=rows.find(k);Row temporary;const Row*r;if(it==rows.end()){temporary=initial(own,board,p,round,hist,legal,live,street,remaining,price);r=&temporary;}else r=&it->second;auto pi=matching(*r,average);std::vector<double>v(legal.size(),0.);for(size_t a=0;a<r->actions.size();++a){auto j=std::find(legal.begin(),legal.end(),r->actions[a]);if(j==legal.end())throw std::runtime_error("legal action identity changed");v[j-legal.begin()]=pi[a];}return py::dict("key"_a=py::bytes(k),"probabilities"_a=v,"trained"_a=(it!=rows.end()&&r->averages>0),"warm"_a=r->warm,"actions"_a=r->actions,"visits"_a=r->visits,"averages"_a=r->averages);}
 // Frozen-policy conditional EV: all legal root actions share worlds and action
 // randomness. All-in suffix equity is cached by visible street within a world.
 py::dict root_ev(const std::vector<V>&hands,int samples,uint64_t seed,double limit){
  if(samples<1||samples>4096||limit<=0||limit>90)throw std::invalid_argument("bounded root EV budget");
  pn::State initial_state(spec);for(int p=0;p<2;++p)if(initial_state.engine.remaining[p]+initial_state.engine.live[p]!=100)throw std::invalid_argument("HU50 EV only");
  for(int c=0;c<4;++c)initial_state.apply(c);V actions=initial_state.legal_actions();std::mt19937_64 chance(seed);py::list output;auto start=std::chrono::steady_clock::now();
  for(auto own:hands){std::vector<double>sum(actions.size(),0.),square(actions.size(),0.);int done=0;
   for(int sample=0;sample<samples;++sample){if(std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()>limit)break;
    V deck;for(int c=0;c<52;++c)if(c!=own[0]&&c!=own[1])deck.push_back(c);std::shuffle(deck.begin(),deck.end(),chance);V world{own[0],own[1]};world.insert(world.end(),deck.begin(),deck.begin()+7);uint64_t action_seed=chance(),future_seed=chance();double cached[4]{-1,-1,-1,-1};
    for(size_t a=0;a<actions.size();++a){pn::State state(spec);for(int j=0;j<4;++j)state.apply(world[j]);state.apply(actions[a]);std::mt19937_64 arng(action_seed);double result=0.;bool conditioned=false;
     while(!state.terminal()){
      if(state.chance()){if(state.engine.remaining[0]==0&&state.engine.remaining[1]==0&&state.board.size()<5){int r=state.engine.round;if(cached[r]<0)cached[r]=equity_prefix(V(world.begin(),world.begin()+4),state.board,16,future_seed);result=50*(2*cached[r]-1);conditioned=true;break;}fill(state,world);continue;}
      const auto&e=state.engine;auto k=key(state.holes[e.actor],state.board,e.actor,e.round,e.history);auto it=rows.find(k);Row temporary;const Row*row;
      if(it==rows.end()){temporary=initial(state.holes[e.actor],state.board,e.actor,e.round,e.history,state.legal_actions(),e.live,e.street,e.remaining,e.price);row=&temporary;}else row=&it->second;
      auto pi=matching(*row,true);std::discrete_distribution<int>d(pi.begin(),pi.end());state.apply(row->actions[d(arng)]);
     }
     if(!conditioned)result=value(state);sum[a]+=result;square[a]+=result*result;
    }++done;
   }
   output.append(py::dict("own"_a=own,"samples"_a=done,"sum"_a=sum,"square"_a=square));if(done<samples)break;
  }
  return py::dict("actions"_a=actions,"rows"_a=output,"seconds"_a=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count(),"requested_per_class"_a=samples);
 }
 py::dict trace(const V&world,int owner,const V&plan){begin=std::chrono::steady_clock::now();deadline=2.;nodes=0;pending.clear();scripted=true;script=plan;script_at=0;bool complete=false;double val=0.;std::mt19937_64 rng(1);try{pn::State s(spec);for(int j=0;j<4;++j)s.apply(world[j]);val=walk(std::move(s),owner,world,rng);complete=true;}catch(const NeedAction&){}scripted=false;py::list updates;if(complete)for(auto&[k,r]:rows){auto it=pending.find(&r);if(it!=pending.end()){auto&u=it->second;updates.append(py::dict("key"_a=py::bytes(k),"actions"_a=r.actions,"R"_a=u.R,"A"_a=u.A));}}pending.clear();return py::dict("complete"_a=complete,"need"_a=need,"updates"_a=updates,"value"_a=val);}
 py::dict stats(){size_t actions=0,visited=0,averaged=0;for(auto&[k,r]:rows){actions+=r.actions.size();visited+=r.visits>0;averaged+=r.averages>0;}return py::dict("estimated_row_bytes"_a=allocated,"iterations"_a=iterations,"rows"_a=rows.size(),"action_entries"_a=actions,"regret_visited"_a=visited,"average_visited"_a=averaged);}
 void save(const std::string&path,const std::string&id){std::ofstream f(path,std::ios::binary);auto n=[&](uint64_t x){f.write((char*)&x,8);};auto str=[&](const std::string&s){n(s.size());f.write(s.data(),s.size());};str("sparse-native-v1");str(id);n(iterations);std::ostringstream state;state<<master;str(state.str());n(rows.size());std::vector<std::string>keys;for(auto&entry:rows)keys.push_back(entry.first);std::sort(keys.begin(),keys.end());for(auto&k:keys){auto&r=rows.at(k);str(k);n(r.actions.size());for(I a:r.actions)f.write((char*)&a,8);for(double x:r.R)f.write((char*)&x,8);for(double x:r.A)f.write((char*)&x,8);for(double x:r.prior)f.write((char*)&x,8);n(r.visits);n(r.averages);n(r.warm);}if(!f)throw std::runtime_error("checkpoint write");}
 void restore(const std::string&path,const std::string&id){std::ifstream f(path,std::ios::binary);auto n=[&](){uint64_t x=0;f.read((char*)&x,8);if(!f)throw std::runtime_error("checkpoint read");return x;};auto str=[&](){auto size=n();if(size>100000)throw std::runtime_error("checkpoint string cap");std::string s(size,0);f.read(s.data(),size);return s;};if(str()!="sparse-native-v1"||str()!=id)throw std::runtime_error("checkpoint identity");iterations=n();std::istringstream state(str());state>>master;auto count=n();if(count>maxrows)throw std::runtime_error("checkpoint row budget");std::unordered_map<std::string,Row>loaded;for(size_t i=0;i<count;++i){auto k=str();size_t a=n();if(a==0||a>256)throw std::runtime_error("checkpoint actions");Row r;r.actions.resize(a);r.R.resize(a);r.A.resize(a);r.prior.resize(a);for(auto&v:r.actions)f.read((char*)&v,8);for(auto&v:r.R)f.read((char*)&v,8);for(auto&v:r.A)f.read((char*)&v,8);for(auto&v:r.prior)f.read((char*)&v,8);r.visits=n();r.averages=n();r.warm=n();loaded.emplace(k,std::move(r));}if(!f)throw std::runtime_error("checkpoint truncated");rows.swap(loaded);allocated=0;for(auto&[k,r]:rows)allocated+=sizeof(Row)+k.size()+128+32*r.actions.size();}
};
static double equity_prefix(const V&holes,const V&board,int samples,uint64_t seed){if(holes.size()!=4||(board.size()!=0&&board.size()!=3&&board.size()!=4&&board.size()!=5))throw std::invalid_argument("own/opponent settled holes and public prefix");std::set<I>used;for(I c:holes)if(c<0||c>=52||!used.insert(c).second)throw std::invalid_argument("private cards");for(I c:board)if(c<0||c>=52||!used.insert(c).second)throw std::invalid_argument("public cards");V deck;for(int c=0;c<52;++c)if(!used.count(c))deck.push_back(c);int a[7]{int(holes[0]),int(holes[1])},b[7]{int(holes[2]),int(holes[3])};for(size_t j=0;j<board.size();++j)a[2+j]=b[2+j]=board[j];double win=0.;uint64_t count=0;auto settle=[&](){auto x=fast(a),y=fast(b);win+=(x>y?1.:x==y?.5:0.);++count;};
 if(board.size()==5)settle();else if(board.size()==4){for(I c:deck){a[6]=b[6]=c;settle();}}else if(board.size()==3){for(size_t i=0;i<deck.size();++i)for(size_t j=i+1;j<deck.size();++j){a[5]=b[5]=deck[i];a[6]=b[6]=deck[j];settle();}}else{if(samples<1||samples>100000)throw std::invalid_argument("sample budget");std::mt19937_64 rng(seed);for(int j=0;j<samples;++j){std::shuffle(deck.begin(),deck.end(),rng);for(int k=0;k<5;++k)a[2+k]=b[2+k]=deck[k];settle();}}return win/count;}
PYBIND11_MODULE(_sparse_qualification,m){py::class_<Sparse>(m,"Sparse")
 .def(py::init<py::object,py::dict,uint64_t,bool,bool,size_t,size_t>())
 .def("root_ev",&Sparse::root_ev).def("seed_preflop",&Sparse::seed_preflop).def("trace",&Sparse::trace).def("step",&Sparse::step).def("query",&Sparse::query).def("stats",&Sparse::stats)
 .def("save",&Sparse::save).def("restore",&Sparse::restore);
 m.def("equity_prefix",&equity_prefix);
 m.def("visible_rank",&visible_rank);
 m.def("pre_equities",[](const std::vector<V>&hands,int samples,uint64_t seed){std::vector<double>out;std::mt19937_64 rng(seed);for(auto own:hands){std::set<I>used(own.begin(),own.end());V deck;for(int c=0;c<52;++c)if(!used.count(c))deck.push_back(c);double sum=0.;for(int j=0;j<samples;++j){std::shuffle(deck.begin(),deck.end(),rng);V hole{own[0],own[1],deck[0],deck[1]},board(deck.begin()+2,deck.begin()+7);sum+=equity_prefix(hole,board,1,0);}out.push_back(sum/samples);}return out;});
 m.def("terminal_value",[](py::object game,const V&world,const V&prefix){auto spec=std::make_shared<pn::Spec>(game);pn::State s(spec);for(int j=0;j<4;++j)s.apply(world[j]);for(I a:prefix){while(s.chance()&&!s.terminal())s.apply(world[4+s.board.size()]);s.apply(a);}while(s.chance()&&!s.terminal())s.apply(world[4+s.board.size()]);if(!s.terminal())throw std::invalid_argument("terminal prefix needed");auto&e=s.engine;if(e.folded[0])return-e.live[0]/2.;if(e.folded[1])return e.live[1]/2.;V a=s.holes[0],b=s.holes[1];a.insert(a.end(),s.board.begin(),s.board.end());b.insert(b.end(),s.board.begin(),s.board.end());return (pn::rank7(a)>pn::rank7(b)?1.:pn::rank7(a)<pn::rank7(b)?-1.:0.)*std::min(e.live[0],e.live[1])/2.;});
}
