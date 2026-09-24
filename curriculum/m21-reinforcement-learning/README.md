# M21 · Reinforcement Learning for Trading

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T5 · AI for Trading |
| Weeks | 42 |
| Hours | 12 guided |
| Labs | [21a](lab_21a_reinforcement_learning.py) — Q-learning policy, rule baseline, costs in the reward, seed spread |
| Library | `cfmat.ml.reinforcement` |
| Prerequisites | [M19](../m19-machine-learning/README.md) |
| Committed topics | Reinforcement learning |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Reinforcement learning promises agents that learn to trade by trial and error. In practice,
rewards are noisy, environments are hard to make realistic, and results swing with the random
seed. This one-week module takes a Q-learning agent apart — state, action, reward, Bellman update,
exploration — so learners can judge RL claims and design fair environments for execution or
allocation capstones.

## Learning outcomes

By the end of the module you can:

1. Formulate trading and execution problems as Markov decision processes: states, actions, rewards, transitions.
2. Implement and explain tabular Q-learning (`cfmat.ml.reinforcement.QLearningTrader`) and read its policy.
3. Include transaction costs in the reward and explain how they change the learned policy.
4. Evaluate an agent against a simple rule baseline and buy and hold, out of sample.
5. Report seed sensitivity and explain why noisy rewards plus fast learning give unstable policies.
6. Describe DQN and policy-gradient methods (PPO) and what they change in the loop.

## Before you start

- M19 complete; M20 recommended.
- Read Sutton and Barto, ch. 1 and 6.

## Weekly plan

### Week 42 — Agents, rewards and costs — Q-learning taken apart

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M20 · 15–60 MDPs, value functions, Bellman equations · 60–70 break · 70–120 Q-learning: the update rule, learning rate, discount, exploration · 120–170 live: Lab 21a §1–§2 — train, read the policy, compare with the rule it should discover · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 environment design: costs, position limits, latency; reward shaping (P&L, risk-adjusted, drawdown penalties) · 60–70 break · 70–130 workshop: Lab 21a §3–§4 — costs in the reward; seed spread; learning-rate sensitivity · 130–170 DQN and PPO: function approximation and policy gradients; RL for execution (link to M15) · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 21a exercises: volatility regime in the state · 100–120 blockers |
| OH · Wed · 60 min | RL capstone scoping |
| C2 · Thu · 120 min | 0–60 exercise: an MLPRegressor Q-function (the core idea of DQN) · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 21 · 20–50 critique a published RL trading result · 50–60 preview of M22 |
| Self-study · ~6 h | Sutton and Barto ch. 6, 13; ML signal assignment (due Sunday) |

## Labs

**Lab 21a — reinforcement learning for trading** (`lab_21a_reinforcement_learning.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Train and read | Q-table after 30 episodes | Best action follows the last return (planted momentum) |
| 2. Out of sample | Agent vs sign-of-last-return rule vs buy and hold | Agent ≈ the rule; both beat buy and hold here |
| 3. Costs | 0, 5, 20 bp in the reward | Fewer position changes as costs rise; at 20 bp it learns to stay out |
| 4. Seeds | Ten seeds; a 20× larger learning rate | Report the distribution; fast learning is unstable |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quiz 21 | quizzes (10%) | Fri W42 | Concepts |
| Lab 21a | labs (20%) | Sun W42 | Runs; seed spread reported |

## Common mistakes

- Reporting the best seed → report the distribution (section 4).
- Rewards without costs → agents that churn; section 3.
- Evaluating on the training period → freeze the policy, trade the test period.
- Environments that let the agent see the next return → state built from past returns only.

## Readings

- Sutton and Barto, *Reinforcement Learning: An Introduction*, ch. 1–6, 13.
- Mnih et al. (2015), "Human-level control through deep reinforcement learning" (DQN).
- Schulman et al. (2017), "Proximal Policy Optimization Algorithms".
- Nevmyvaka, Feng and Kearns (2006), "Reinforcement learning for optimized trade execution".

## Instructor notes

- Owner: ML/DL and advanced strategies lead.
- Resist showing impressive RL equity curves; show the seed distribution first.
- RL capstones must beat a strong classical baseline (for execution: Almgren–Chriss from M15).
