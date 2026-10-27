// Experimental complete-game oracle. Reuses the original NativeState unchanged.
#include "g11_native_state.h"
#include <random>
#include <set>

using pokerid7rules::I;
using pokerid7rules::V;
using pokerid7rules::require;
using pokerid11state::Spec;
using pokerid11state::State;

static std::shared_ptr<Spec> checked(py::object game) {
  auto spec=std::make_shared<Spec>(game);
  require(!spec->fixture && spec->roots.empty(),"unconditioned full-deck game required");
  State root(spec);
  require(root.engine.n==2 && root.engine.initial==V({2,2}) && root.engine.bb==2 &&
          root.engine.bba==0 && root.engine.num==0 && root.engine.den==1 && root.engine.cap==-1,
          "only HU2/2chips BB2 noante norake is supported");
  require(root.engine.remaining==V({1,0}),"BB must be forced all-in");
  return spec;
}

static I draw(State& state,std::mt19937_64& rng) {
  require(state.chance() && !state.deck.empty(),"native card chance required");
  std::uniform_int_distribution<size_t> index(0,state.deck.size()-1);
  I card=state.deck[index(rng)];state.apply(card);return card;
}

static V settle_deal(py::object game,const V& cards,bool fold) {
  require(cards.size()==9 && std::set<I>(cards.begin(),cards.end()).size()==9 &&
          *std::min_element(cards.begin(),cards.end())>=0 && *std::max_element(cards.begin(),cards.end())<52,
          "nine distinct native card IDs required");
  State state(checked(game));
  for(size_t i=0;i<4;++i)state.apply(cards[i]);
  require(state.actor()==0 && state.legal_actions()==V({0,1}),"complete root must be fold/call only");
  state.apply(fold?0:1);
  if(!fold)for(size_t i=4;i<9;++i){require(state.chance(),"unexpected postflop decision");state.apply(cards[i]);}
  require(state.terminal(),"real native terminal required");
  return state.settlement()["net"].cast<V>();
}

static py::dict sample(py::object game,const V& hero,uint64_t samples,uint64_t seed) {
  require(hero.size()==2 && hero[0]!=hero[1] && hero[0]>=0 && hero[0]<52 && hero[1]>=0 && hero[1]<52,
          "two distinct native hero cards required");
  require(samples>=1 && samples<=1000000,"finite sample budget required");
  auto spec=checked(game);std::mt19937_64 rng(seed);
  uint64_t wins=0,losses=0,ties=0;
  for(uint64_t i=0;i<samples;++i){
    State state(spec);state.apply(hero[0]);state.apply(hero[1]);draw(state,rng);draw(state,rng);
    require(state.actor()==0 && state.legal_actions()==V({0,1}),"root action identity changed");
    state.apply(1);
    while(!state.terminal())draw(state,rng); // Throws on ANY unexpected decision.
    V net=state.settlement()["net"].cast<V>();
    require(net.size()==2 && net[0]+net[1]==0,"native chip conservation required");
    if(net[0]==2)++wins;else if(net[0]==-2)++losses;else{require(net[0]==0,"unexpected terminal payoff");++ties;}
  }
  py::dict result;result["wins"]=wins;result["losses"]=losses;result["ties"]=ties;
  result["samples"]=samples;result["seed"]=seed;return result;
}

PYBIND11_MODULE(pokerid_onebb,m) {
  m.def("sample",&sample);m.def("settle_deal",&settle_deal,py::arg("game"),py::arg("cards"),py::arg("fold")=false);
}
