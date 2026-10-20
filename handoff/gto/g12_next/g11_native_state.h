// Copyright 2026 Poker ID contributors. Apache-2.0.
#pragma once
#include "g11_rules_embed.h"
#include <memory>
namespace pokerid11state {
using namespace pokerid7rules;
struct Spec {
 py::list stacks;py::dict rules;bool fixture=false;V hole_deck,fixture_board,roots;std::string public_json;
 Spec(py::object game){stacks=game.attr("stacks").cast<py::list>();rules=game.attr("_native_rules").cast<py::dict>();roots=game.attr("root_actions").cast<V>();public_json=game.attr("_public_config_json").cast<std::string>();auto f=game.attr("fixture");fixture=!f.is_none();if(fixture){auto d=f.cast<py::dict>();hole_deck=d["hole_deck"].cast<V>();fixture_board=d["board"].cast<V>();}}
};
inline std::string ints(const V& a){std::string s="[";for(size_t i=0;i<a.size();++i){if(i)s+=',';s+=std::to_string(a[i]);}return s+"]";}
struct State {
 std::shared_ptr<Spec> spec;Ledger engine;V deck,board,replay;std::vector<V> holes;int dealt=0,target=0;
 explicit State(std::shared_ptr<Spec> p):spec(std::move(p)),engine(spec->stacks,spec->rules),holes(engine.n){if(spec->fixture)deck=spec->hole_deck;else{deck.resize(52);std::iota(deck.begin(),deck.end(),0);}for(I a:spec->roots)apply(a);}
 bool terminal()const{return engine.done&&dealt>=2*engine.n;}
 int actor()const{if(terminal())return -4;if(dealt<2*engine.n||board.size()<size_t(target))return -1;return engine.actor;}
 bool chance()const{return actor()==-1;}
 std::vector<std::pair<I,double>> chances()const{require(chance(),"not chance node");std::vector<std::pair<I,double>> a;double p=1./deck.size();a.reserve(deck.size());for(I c:deck)a.push_back({c,p});return a;}
 void advance(){if(dealt<2*engine.n||board.size()<size_t(target))return;while(!engine.done){if(engine.actor>=0){if(spec->fixture&&engine.round<3){engine.act(1);continue;}return;}engine.next_round();target=std::array<int,4>{0,3,4,5}[engine.round];if(spec->fixture)board=V(spec->fixture_board.begin(),spec->fixture_board.begin()+target);if(board.size()<size_t(target))return;}}
 void apply(I a){require(!terminal(),"terminal action");if(chance()){auto it=std::find(deck.begin(),deck.end(),a);require(it!=deck.end(),"invalid/duplicate card");deck.erase(it);if(dealt<2*engine.n){holes[dealt/2].push_back(a);++dealt;}else board.push_back(a);}else{require(a>=0&&a!=2,"illegal game action");I raw=a==3?-3:(a>=4?a-2:a);require(engine.valid(raw),"illegal game action");engine.act(raw);}replay.push_back(a);advance();}
 std::vector<std::pair<I,I>> ranges()const{require(actor()>=0,"decision required");return engine.game_ranges();}
 V legal_actions()const{if(terminal())return {};if(chance())return deck;V v;for(auto [lo,hi]:ranges()){if(hi-lo>5000000)throw std::length_error("legal enumeration guard, no pruning");for(I a=lo;a<=hi;++a)v.push_back(a);}return v;}
 std::string info(int p)const{require(p>=0&&p<engine.n,"seat required");std::string h="[";for(size_t i=0;i<engine.history.size();++i){if(i)h+=',';auto row=engine.history[i];h+='[';for(int j=0;j<5;++j){if(j)h+=',';h+=std::to_string(row[j]);}h+=']';}h+=']';return "{\"betting_history\":"+h+",\"board\":"+ints(board)+",\"hand\":"+ints(holes[p])+",\"public_config\":"+spec->public_json+",\"seat\":"+std::to_string(p)+"}";}
 py::dict settlement()const{require(terminal(),"not terminal");std::vector<V> ranks;for(auto hole:holes){if(board.size()==5){hole.insert(hole.end(),board.begin(),board.end());ranks.push_back(rank7(hole));}else ranks.push_back({0});}return engine.settle(ranks,board.size()>=3);}
 double utility(int p)const{require(p>=0&&p<engine.n,"seat required");return settlement()["net"].cast<V>()[p];}
 std::vector<double> returns()const{if(!terminal())return std::vector<double>(engine.n,0.);auto v=settlement()["net"].cast<V>();return std::vector<double>(v.begin(),v.end());}
 py::dict audit()const{auto d=engine.audit();d["deck"]=deck;d["holes"]=holes;d["board"]=board;d["dealt"]=dealt;d["target"]=target;d["replay"]=replay;return d;}
};
}
