// Existing sparse native support + PCS exact private integration, one joint game.
// Including the old module preserves its implementation; only _integrated init
// is invoked here. Its public query supplies the SAME generic action selector.
#include "sparse_native.cc"
class Integrated {
 using Terminal=int(*)(int,const int*,const int*,const double*,double*,double*);
 using World=int(*)(const int*,int*,int*,int*);
 std::shared_ptr<pn::Spec>spec;Sparse selector;Terminal terminal;World worldfn;
 std::vector<int>classes;std::unordered_map<std::string,Row>rows;
 std::unordered_map<Row*,Pending>pending;std::mt19937_64 master;
 size_t cap;uint64_t t=0,nodes=0;double eps;bool halted=false;
 int holes[2162],flags[1081],ranks[1081];V board;
 std::vector<std::string>suffix[4];std::unordered_map<std::string,V>expansions;double maxweight=0.;
 std::string key(const V&own,const V&pub,int actor,int round,const H&hist,int nuts=-1)const{
  std::string k=history_key(round,hist);k.push_back(char(actor));int16_t h=classes[own[0]*52+own[1]];k.append((char*)&h,2);
  // Retain own169 and ALL earlier strategic signals (no private-memory loss).
  for(int n:{3,4,5})if(pub.size()>=size_t(n)){
   V prefix(pub.begin(),pub.begin()+n);uint32_t signal=shared_signal(own,prefix);k.append((char*)&signal,4);
   int o[2]{int(own[0]),int(own[1])},b[5]{};std::copy(prefix.begin(),prefix.end(),b);
   k.push_back(char(n==5?(nuts<0?fs_nuts(o,b):nuts):fs_feature(o,b,n)));
   std::set<int>unique;for(I c:prefix)unique.insert(c/4);k.push_back(char(unique.size()<size_t(n)));
  }return k;
 }
 Row initial(const V&own,const V&pub,int p,int round,const H&hist,const V&legal,const V&live,const V&street,const V&remaining,I price){
  auto d=selector.query(own,pub,p,round,hist,legal,live,street,remaining,price,true);
  Row r;r.actions=d["actions"].cast<V>();auto all=d["probabilities"].cast<std::vector<double>>();
  for(I a:r.actions)r.prior.push_back(all[std::find(legal.begin(),legal.end(),a)-legal.begin()]);
  r.R=r.prior;r.A=r.prior;for(auto&x:r.R)x*=1e-6;for(auto&x:r.A)x*=1e-3;r.warm=d["warm"].cast<bool>();return r;
 }
 static std::vector<double>policy(const Row&r,bool average){auto&v=average?r.A:r.R;double z=std::accumulate(v.begin(),v.end(),0.);if(z<=0)return r.prior;auto out=v;for(auto&x:out)x/=z;return out;}
 void grow(Row&r,const V&legal,const std::string&tag){
  auto it=expansions.find(tag);if(it==expansions.end())return;V actions=r.actions;
  for(I a:it->second)if(std::find(legal.begin(),legal.end(),a)!=legal.end())actions.push_back(a);
  std::sort(actions.begin(),actions.end());actions.erase(std::unique(actions.begin(),actions.end()),actions.end());if(actions==r.actions)return;
  std::vector<double>R(actions.size(),0.),A=R,prior(actions.size(),1e-6);
  for(size_t j=0;j<r.actions.size();++j){auto at=std::find(actions.begin(),actions.end(),r.actions[j])-actions.begin();R[at]=r.R[j];A[at]=r.A[j];prior[at]=r.prior[j];}
  double sum=std::accumulate(prior.begin(),prior.end(),0.);for(auto&x:prior)x/=sum;r.actions=actions;r.R=R;r.A=A;r.prior=prior;
 }
 void cache(int round){if(!suffix[round].empty())return;V prefix(board.begin(),board.begin()+std::array<int,4>{0,3,4,5}[round]);
  for(int h=0;h<1081;++h){V own{holes[2*h],holes[2*h+1]};auto k=key(own,prefix,0,round,{},flags[h]&1);suffix[round].push_back(k.substr(2));}
 }
 Row& get(const pn::State&s,int h){auto&e=s.engine;cache(e.round);V own{holes[2*h],holes[2*h+1]};auto tag=history_key(e.round,e.history);auto k=tag;k.push_back(char(e.actor));k+=suffix[e.round][h];
  auto it=rows.find(k);if(it!=rows.end()){grow(it->second,s.legal_actions(),tag);return it->second;}
  if(rows.size()>=cap)throw std::runtime_error("integrated row budget; stop without resampling");
  auto r=initial(own,s.board,e.actor,e.round,e.history,s.legal_actions(),e.live,e.street,e.remaining,e.price);grow(r,s.legal_actions(),tag);return rows.emplace(k,std::move(r)).first->second;
 }
 Pending& add(Row&r){auto [it,fresh]=pending.try_emplace(&r);if(fresh){it->second.R.assign(r.actions.size(),0.);it->second.A.assign(r.actions.size(),0.);}return it->second;}
 void prepare(const V&b){board=b;if(board.size()!=5)throw std::invalid_argument("complete sampled public board");int cs[5];std::copy(board.begin(),board.end(),cs);if(worldfn(cs,holes,flags,ranks)!=1081)throw std::invalid_argument("public card removal");
  for(auto&x:suffix)x.clear();
 }
 void fill(pn::State&s){while(s.chance()&&!s.terminal())s.apply(board[s.board.size()]);}
 pn::State root(){pn::State s(spec);int count=0;for(int c=0;c<52&&count<4;++c)if(std::find(board.begin(),board.end(),c)==board.end()){s.apply(c);++count;}return s;}
 struct Node{std::vector<Row*>row;std::vector<std::vector<double>>pi;int action,player;double q,prefix;std::vector<double>ownreach;};
 py::dict collect(int owner,std::mt19937_64&rng,const V*script=nullptr){
  pn::State s=root();std::vector<Node>path;std::vector<double>reach[2]{std::vector<double>(1081,1.),std::vector<double>(1081,1.)};double prefix=1.;size_t at=0;
  while(true){fill(s);if(s.terminal())break;if(++nodes>1000)throw std::runtime_error("integrated public path budget; stop");
   Node n;n.player=s.engine.actor;n.prefix=prefix;n.ownreach=reach[owner];std::vector<double>proposal;
   for(int h=0;h<1081;++h){Row&r=get(s,h);if(h==0)proposal.assign(r.actions.size(),0.);else if(r.actions!=n.row[0]->actions)throw std::runtime_error("private-dependent legal support");n.row.push_back(&r);n.pi.push_back(policy(r,false));for(size_t a=0;a<proposal.size();++a)proposal[a]+=n.pi.back()[a]/1081.;}
   for(auto&x:proposal)x=(1-eps)*x+eps/proposal.size();
   if(script){if(at==script->size())return py::dict("complete"_a=false,"need"_a=proposal);n.action=(*script)[at++];if(n.action<0||size_t(n.action)>=proposal.size())throw std::invalid_argument("public action plan");}
   else{std::discrete_distribution<int>d(proposal.begin(),proposal.end());n.action=d(rng);}
   n.q=proposal[n.action];prefix*=n.q;if(prefix<1e-100||!std::isfinite(prefix))throw std::runtime_error("importance weight budget; stop without resampling");maxweight=std::max(maxweight,1/prefix);
   for(int h=0;h<1081;++h)reach[n.player][h]*=n.pi[h][n.action];s.apply(n.row[0]->actions[n.action]);path.push_back(std::move(n));
  }
  std::vector<double>mass(1081),win(1081),v(1081);
  if(terminal(1081,holes,ranks,reach[1-owner].data(),mass.data(),win.data()))throw std::runtime_error("private integration");
  auto&e=s.engine;double c0,c1;
  if(e.folded[0]||e.folded[1]){c0=e.folded[0]?-e.live[0]/2.:e.live[1]/2.;c1=0.;}
  else{c0=-std::min(e.live[0],e.live[1])/2.;c1=std::min(e.live[0],e.live[1]);}
  for(int h=0;h<1081;++h)v[h]=(owner==0?c0*mass[h]+c1*win[h]:-(c0+c1)*mass[h]+c1*win[h])/1070190.;
  for(auto it=path.rbegin();it!=path.rend();++it){auto&n=*it;
   for(int h=0;h<1081;++h){double child=v[h]/n.q;
    if(n.player==owner){Row&r=*n.row[h];auto&u=add(r);double val=n.pi[h][n.action]*child;
     for(size_t a=0;a<r.actions.size();++a){u.R[a]+=((int(a)==n.action?child:0.)-val)/n.prefix;u.A[a]+=(t+1)*n.ownreach[h]*n.pi[h][a]/(1081.*n.prefix);}
     u.visits++;u.averages+=n.ownreach[h]>0;v[h]=val;
    }else v[h]=child;
   }
  }
  double ev=std::accumulate(v.begin(),v.end(),0.);return py::dict("complete"_a=true,"probability"_a=prefix,"value"_a=ev);
 }
public:
 Integrated(py::object game,py::dict data,uint64_t seed,size_t rowcap,uintptr_t term,uintptr_t world,double epsilon):spec(std::make_shared<pn::Spec>(game)),selector(game,data,seed,false,true,rowcap,1000000),terminal((Terminal)term),worldfn((World)world),master(seed),cap(rowcap),eps(epsilon){
  if(!terminal||!worldfn||eps<=0||eps>1)throw std::invalid_argument("integration callbacks/full-support proposal");classes=data["classes"].cast<std::vector<int>>();pn::State s(spec);if(s.engine.n!=2||s.engine.bb!=2||s.engine.bba||s.engine.num)throw std::invalid_argument("isolated HU zeroante/rake bb2 only");
 }
 void expand_support(int round,const H&hist,const V&actions){
  if(!pending.empty())throw std::runtime_error("support change only between updates");pn::State state(spec);for(int c=0;c<4;++c)state.apply(c);
  auto advance=[&](){while(state.chance()&&!state.terminal())state.apply(4+state.board.size());};
  for(auto h:hist){advance();if(state.terminal()||state.engine.round!=h[0]||state.engine.actor!=h[1])throw std::invalid_argument("support history");state.apply(h[2]==-3?3:h[2]>=2?h[2]+2:h[2]);}
  advance();if(state.terminal()||state.engine.round!=round)throw std::invalid_argument("support public round");auto legal=state.legal_actions();
  for(I a:actions)if(a<=1||std::find(legal.begin(),legal.end(),a)==legal.end())throw std::invalid_argument("support must be native legal raise");
  auto tag=history_key(round,hist);auto&dest=expansions[tag];dest.insert(dest.end(),actions.begin(),actions.end());std::sort(dest.begin(),dest.end());dest.erase(std::unique(dest.begin(),dest.end()),dest.end());
  for(auto&[k,r]:rows)if(k.size()==tag.size()+3+6*round&&k.compare(0,tag.size(),tag)==0)grow(r,legal,tag);
 }
 void seed_preflop(py::list data){if(t||!rows.empty())throw std::runtime_error("bootstrap before learning only");for(auto item:data){auto d=item.cast<py::dict>();Row r;r.actions=d["actions"].cast<V>();r.R=d["R"].cast<std::vector<double>>();r.A=d["A"].cast<std::vector<double>>();r.prior=d["prior"].cast<std::vector<double>>();r.warm=true;rows.emplace(d["key"].cast<std::string>(),r);}}
 py::dict query(const V&own,const V&pub,int p,int round,const H&hist,const V&legal,const V&live,const V&street,const V&remaining,I price,bool average){auto k=key(own,pub,p,round,hist);auto it=rows.find(k);Row tmp;const Row*r;if(it==rows.end()){tmp=initial(own,pub,p,round,hist,legal,live,street,remaining,price);grow(tmp,legal,history_key(round,hist));r=&tmp;}else{grow(it->second,legal,history_key(round,hist));r=&it->second;}auto pi=policy(*r,average);std::vector<double>v(legal.size(),0.);for(size_t a=0;a<r->actions.size();++a){auto j=std::find(legal.begin(),legal.end(),r->actions[a]);if(j==legal.end())throw std::runtime_error("native support identity");v[j-legal.begin()]=pi[a];}return py::dict("key"_a=py::bytes(k),"probabilities"_a=v,"actions"_a=r->actions,"prior"_a=r->prior,"trained"_a=r->visits>0&&r->averages>0,"warm"_a=r->warm,"visits"_a=r->visits,"averages"_a=r->averages);}
 py::dict step(double limit){if(halted)throw std::runtime_error("previous incomplete pair halted solver");auto start=std::chrono::steady_clock::now();nodes=0;maxweight=0.;pending.clear();V cards(52);std::iota(cards.begin(),cards.end(),0);std::shuffle(cards.begin(),cards.end(),master);V b(cards.begin(),cards.begin()+5);uint64_t seeds[2]{master(),master()};bool complete=false;std::string error;
  try{prepare(b);for(int p=0;p<2;++p){std::mt19937_64 rng(seeds[p]);collect(p,rng);if(std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()>limit)throw std::runtime_error("pair time budget; halt without resampling");}
   for(auto&[r,u]:pending){for(size_t a=0;a<r->R.size();++a){if(!std::isfinite(u.R[a]+u.A[a]))throw std::runtime_error("nonfinite integrated update");}}
   for(auto&[r,u]:pending){for(size_t a=0;a<r->R.size();++a){r->R[a]=std::max(0.,r->R[a]+u.R[a]);r->A[a]+=u.A[a];}r->visits+=u.visits;r->averages+=u.averages;}++t;complete=true;
  }catch(const std::runtime_error&e){error=e.what();halted=true;}pending.clear();return py::dict("complete"_a=complete,"error"_a=error,"iterations"_a=t,"nodes"_a=nodes,"rows"_a=rows.size(),"max_inverse_proposal"_a=maxweight);
 }
 py::dict trace(const V&b,int owner,const V&plan){prepare(b);nodes=0;pending.clear();std::mt19937_64 rng(1);auto out=collect(owner,rng,&plan);py::list updates;if(out["complete"].cast<bool>())for(auto&[k,r]:rows){auto it=pending.find(&r);if(it!=pending.end())updates.append(py::dict("key"_a=py::bytes(k),"actions"_a=r.actions,"R"_a=it->second.R,"A"_a=it->second.A));}pending.clear();out["updates"]=updates;return out;}
 py::dict stats(){size_t v=0,a=0;for(auto&[k,r]:rows){v+=r.visits>0;a+=r.averages>0;}return py::dict("iterations"_a=t,"rows"_a=rows.size(),"regret_visited"_a=v,"average_visited"_a=a,"halted"_a=halted);}
 void save(const std::string&path,const std::string&id){std::ofstream f(path,std::ios::binary);auto num=[&](uint64_t n){f.write((char*)&n,8);};auto str=[&](const std::string&s){num(s.size());f.write(s.data(),s.size());};str("integrated-private-v2");str(id);num(t);num(halted);std::ostringstream rng;rng<<master;str(rng.str());num(expansions.size());std::vector<std::string>extra_keys;for(auto&x:expansions)extra_keys.push_back(x.first);std::sort(extra_keys.begin(),extra_keys.end());for(auto&k:extra_keys){auto&v=expansions.at(k);str(k);num(v.size());for(I a:v)f.write((char*)&a,8);}num(rows.size());std::vector<std::string>keys;for(auto&x:rows)keys.push_back(x.first);std::sort(keys.begin(),keys.end());for(auto&k:keys){auto&r=rows.at(k);str(k);num(r.actions.size());for(I x:r.actions)f.write((char*)&x,8);for(auto*v:{&r.R,&r.A,&r.prior})for(double x:*v)f.write((char*)&x,8);num(r.visits);num(r.averages);num(r.warm);}if(!f)throw std::runtime_error("integrated checkpoint write");}
 void restore(const std::string&path,const std::string&id){std::ifstream f(path,std::ios::binary);auto num=[&](){uint64_t n=0;f.read((char*)&n,8);if(!f)throw std::runtime_error("checkpoint read");return n;};auto str=[&](){auto n=num();if(n>100000)throw std::runtime_error("checkpoint string cap");std::string s(n,0);f.read(s.data(),n);return s;};if(str()!="integrated-private-v2"||str()!=id)throw std::runtime_error("integrated identity");t=num();halted=num();std::istringstream rng(str());rng>>master;expansions.clear();auto ne=num();if(ne>10000)throw std::runtime_error("support registry cap");for(uint64_t i=0;i<ne;++i){auto k=str();auto n=num();if(n>256)throw std::runtime_error("support action cap");V v(n);for(auto&a:v)f.read((char*)&a,8);expansions.emplace(k,v);}auto count=num();if(count>cap)throw std::runtime_error("checkpoint row cap");rows.clear();for(uint64_t i=0;i<count;++i){auto k=str();auto n=num();if(!n||n>256)throw std::runtime_error("checkpoint action cap");Row r;r.actions.resize(n);r.R.resize(n);r.A.resize(n);r.prior.resize(n);for(auto&x:r.actions)f.read((char*)&x,8);for(auto*v:{&r.R,&r.A,&r.prior})for(auto&x:*v){f.read((char*)&x,8);if(!std::isfinite(x)||x<0)throw std::runtime_error("checkpoint values");}r.visits=num();r.averages=num();r.warm=num();rows.emplace(k,r);}if(!f||!rng)throw std::runtime_error("checkpoint truncated");}
};
PYBIND11_MODULE(_integrated_qualification,m){py::class_<Integrated>(m,"Integrated").def(py::init<py::object,py::dict,uint64_t,size_t,uintptr_t,uintptr_t,double>()).def("expand_support",&Integrated::expand_support).def("step",&Integrated::step).def("query",&Integrated::query).def("seed_preflop",&Integrated::seed_preflop).def("trace",&Integrated::trace).def("stats",&Integrated::stats).def("save",&Integrated::save).def("restore",&Integrated::restore);}
