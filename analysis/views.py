from os import name
from django.contrib import messages
from typing import ContextManager
from django.contrib.auth import login
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect, render
from merakicommons.container import SearchError
from .models import Playstyle
from .forms import ChampForm
from django.contrib.auth.decorators import login_required

from django_cassiopeia import cassiopeia as cass
from cassiopeia.core.staticdata import champion
from cassiopeia.data import Queue
from datapipelines.common import NotFoundError



@login_required
def home(request):
    context = {}
    try:
        champ = str(request.GET["champion"])
        champions=cass.get_champion(champ, "NA") # manually set region
        summoner = cass.Summoner(name=str(request.GET["summonerName"]), region="NA")
    except (TypeError, SearchError, KeyError):
        messages.warning(request, "Sorry, champion name is incorrect (champion name is case sensitive)")
        return redirect('analysis-search')
    if summoner.exists == False:
        messages.warning(request, "Sorry, summoner name is incorrect")
        return redirect('analysis-search')
    
    context["name"] = summoner.name
    context["champion"] = champ
    context["key"] = str(champions.key)

    history = []
    matches = summoner.match_history
    gamesChecked = 0

    while len(history) < 7 or gamesChecked >= 25:
        for participant in matches[gamesChecked].participants:
            if participant.summoner == summoner and participant.champion == champions:
                history.append(matches[gamesChecked])
        gamesChecked+=1

    if len(history) < 7:
        messages.warning(request, "Sorry, you do not have enough games on your champion in your last 25 games (minimum 7)")
        return redirect('analysis-search')
        
    context["icon"] =  f'analysis/champions/{str(champions.key)}.png'

    goldCounter = 0 
    kdaCounter = 0
    deathCounter = 0
    turretDmg = 0
    objectiveDmg = 0
    dmgDealtCounter = 0
    dmgTakenCounter = 0
    vsnCounter = 0
    csCounter = 0
    baronCounter = 0
    dragCounter = 0
    riftCounter = 0
    inhibCounter = 0
    towerCounter = 0
    ccCounter = 0
    healCounter = 0
    xpCounter = 0
    mitigatedCounter = 0
    firstBloodCounter = 0
    firstTowerCounter = 0

    earlyLead = 0
    midLead = 0
    lateLead = 0

    games_reviewed=0
    for i in range(7):
        match = history[i]
        
        if (match.is_remake == False):
            games_reviewed+=1
            player = match.participants[champions]
            
            for j in match.participants:
                if player.stats.role == match.participants[j].stats.role and player.stats.lane == match.participants[j].stats.lane and player.summoner != match.participants[j].summoner:
                    enemy = match.participants[j]
                    break

            game_length = str(match.duration)
            game_length = game_length.split(":")
            game_length = int(game_length[0]) * 60 + int(game_length[1]) + int(game_length[2])/60
            
            if player.stats.first_blood_kill or player.stats.first_blood_assist:
                firstBloodCounter += 1
            if player.stats.first_tower_kill or player.stats.first_tower_assist:
                firstTowerCounter += 1
            if (player.stats.gold_earned > enemy.stats.gold_earned):
                goldCounter += 1
            if player.stats.inhibitor_takedowns > enemy.stats.inhibitor_takedowns:
                inhibCounter += 1

                
            
            if player.stats.champ_experience > enemy.stats.champ_experience:
                xpCounter += 1

            if (player.stats.deaths < enemy.stats.deaths):
                deathCounter+=1
                
                
            if player.team.baron_kills > enemy.team.baron_kills:
                baronCounter +=1
            if player.team.first_rift_herald == True:
                riftCounter += 0.75
            if player.team.rift_herald_kills == 2:
                riftCounter += 0.5
            if player.team.dragon_kills > enemy.team.dragon_kills:
                dragCounter += 1
            if player.team.tower_kills > enemy.team.tower_kills:
                towerCounter+=1
                

            tempDmgTaken = 0
            tempDmgDealt = 0
            tempTurretDmg = 0
            tempObjDmg = 0
            tempKda = 0
            tempCC = 0
            tempHealing = 0
            tempMitigated = 0

            for j in match.participants:
                if (player.stats.total_damage_dealt_to_champions > match.participants[j].stats.total_damage_dealt_to_champions):
                    tempDmgDealt+=1
                if (player.stats.total_damage_taken > match.participants[j].stats.total_damage_taken):
                    tempDmgTaken+=1
                if player.stats.damage_dealt_to_turrets > match.participants[j].stats.damage_dealt_to_turrets:
                    tempTurretDmg+=1
                if player.stats.damage_dealt_to_objectives - player.stats.damage_dealt_to_turrets > match.participants[j].stats.damage_dealt_to_objectives - match.participants[j].stats.damage_dealt_to_turrets:
                    tempObjDmg+=1
                if (player.stats.kills + player.stats.assists > match.participants[j].stats.kills + match.participants[j].stats.assists):
                    tempKda+=1
                if player.stats.time_CCing_others > match.participants[j].stats.time_CCing_others:
                    tempCC += 1
                if player.stats.total_units_healed > match.participants[j].stats.total_units_healed or player.stats.total_heal > match.participants[j].stats.total_heal:
                    tempHealing +=1
                if player.stats.damage_self_mitigated > match.participants[j].stats.damage_self_mitigated:
                    tempMitigated +=1

            if tempDmgTaken > 6:
                dmgTakenCounter+=1
            if tempDmgDealt > 6:
                dmgDealtCounter+=1
            if tempTurretDmg > 7:
                turretDmg +=1
            if tempObjDmg > 5:
                objectiveDmg +=1
            if tempKda > 6:
                kdaCounter+=1
            if tempCC > 6:
                ccCounter += 1
            if tempHealing > 7:
                healCounter += 1
            if tempMitigated >6:
                mitigatedCounter +=1

            if (player.stats.vision_score > enemy.stats.vision_score):
                vsnCounter+=1

            if (player.stats.total_minions_killed + player.stats.neutral_minions_killed > enemy.stats.total_minions_killed + enemy.stats.neutral_minions_killed):
                csCounter+=1

            print(len(player.timeline.frames), len(enemy.timeline.frames))
            # if the player's gold and xp per min by mins 0-10 are greater than their opponent's, they have an early lead on them
            if len(player.timeline.frames) > 9:
                if ((player.timeline.frames[9].gold_earned - player.timeline.frames[0].gold_earned) / 10 > (enemy.timeline.frames[9].gold_earned - enemy.timeline.frames[0].gold_earned) / 10) and (player.timeline.frames[9].experience - player.timeline.frames[0].experience) / 10 > (enemy.timeline.frames[9].experience - enemy.timeline.frames[0].experience) / 10:
                    earlyLead += 1

            # checking gold and xp per min for mid game
            if len(player.timeline.frames) > 19:
                if ((player.timeline.frames[19].gold_earned - player.timeline.frames[10].gold_earned) / 10 > (enemy.timeline.frames[19].gold_earned - enemy.timeline.frames[10].gold_earned) / 10) and (player.timeline.frames[19].experience - player.timeline.frames[10].experience) / 10 > (enemy.timeline.frames[19].experience - enemy.timeline.frames[10].experience) / 10:
                    midLead += 0.75
            if len(player.timeline.frames) > 29:
                if ((player.timeline.frames[29].gold_earned - player.timeline.frames[20].gold_earned) / 10 > (enemy.timeline.frames[29].gold_earned - enemy.timeline.frames[20].gold_earned) / 10) and (player.timeline.frames[29].experience - player.timeline.frames[20].experience) / 10 > (enemy.timeline.frames[29].experience - enemy.timeline.frames[20].experience) / 10:
                    midLead += 0.25

            # checking gold and xp per min for late game
            if len(player.timeline.frames) > 39:
                if ((player.timeline.frames[39].gold_earned - player.timeline.frames[30].gold_earned) / 10 > (enemy.timeline.frames[39].gold_earned - enemy.timeline.frames[30].gold_earned) / 10) and (player.timeline.frames[39].experience - player.timeline.frames[30].experience) / 10 > (enemy.timeline.frames[39].experience - enemy.timeline.frames[30].experience) / 10:
                    lateLead += 1
            if len(player.timeline.frames) > 49:
                if ((player.timeline.frames[49].gold_earned - player.timeline.frames[40].gold_earned) / 10 > (enemy.timeline.frames[49].gold_earned - enemy.timeline.frames[40].gold_earned) / 10) and (player.timeline.frames[49].experience - player.timeline.frames[40].experience) / 10 > (enemy.timeline.frames[49].experience - enemy.timeline.frames[40].experience) / 10:
                    lateLead += 0.5
            # after 50 mins, everyone has full build and lvl 18, so gold and xp dont matter
                    
                    


    excellent = games_reviewed - round(games_reviewed * 0.33,0)
    good = round(games_reviewed/2,0)
    poor = round(games_reviewed* 0.25, 0)


    aggression = 0
    snowballing = 0
    splitting = 0
    fighting = 0

    work_on_aggression = []
    work_on_snowball = []
    work_on_teamfight = []
    work_on_splitpush = []

    # append what they need to work on into the respective arrays of their playstyle
    # whichever array is shorter, will be what closest represents their playstyle
    # after that, help the player determine what they need to improve upon in their playstyle
    # if multiple arrays are of the same length, the player has a more general playstyle (give them tips to change their playstyle)

    if kdaCounter >= excellent:
        aggression+=1
    else:
        work_on_aggression.append("KP")
    if deathCounter < excellent:
        work_on_aggression.append("DEATHS")
    if vsnCounter >= excellent:
        aggression+=1.75
    else:
        if vsnCounter <= poor:
            work_on_aggression.append("VISION2")
        else:
            work_on_aggression.append("VISION")
    if csCounter < excellent:
        work_on_aggression.append("FARM")
    if xpCounter >= excellent:
        aggression+=1
    else:
        work_on_aggression.append("XP")
    if dragCounter >= excellent:
        aggression+=0.5
    else: 
        work_on_aggression.append("DRAG")
    if baronCounter >= excellent: 
        aggression+=1
    else:
        work_on_aggression.append("BARON")
    if earlyLead >= excellent:
        aggression+=1.5
    else:
        if earlyLead <= poor:
            work_on_aggression.append("EARLY2")
        else:
            work_on_aggression.append("EARLY")
    if midLead >= excellent:
        aggression+=1
    else:
        work_on_aggression.append("MID")
    if firstBloodCounter >= good:
        aggression+=0.25
    else:
        work_on_aggression.append("FB")
    


    if csCounter >= excellent:
        snowballing +=1.5
    else:
        if csCounter <= poor:
            work_on_snowball.append("FARM2")
        else:
            work_on_snowball.append("FARM")
    if kdaCounter >= excellent:
        snowballing +=1
    else:
        work_on_snowball.append("KP")
    if deathCounter >= excellent:
        snowballing +=1
    else:
        work_on_snowball.append("DEATHS")
    if (dragCounter >= good and riftCounter >= good) or dragCounter >= excellent or riftCounter >= excellent: 
        snowballing +=1
    else:
        work_on_snowball.append("OBJECTIVE")
    if baronCounter < excellent:
        work_on_snowball.append("BARON")
    if midLead >= excellent:
        snowballing +=1
    else:
        work_on_snowball.append("MID")
    if towerCounter >= excellent:
        snowballing +=0.5
    else:
        work_on_snowball.append("TOWER")
    if vsnCounter >= excellent:
        snowballing +=0.5
    else:
        work_on_snowball.append("VISION")
    if dmgDealtCounter >= excellent or dmgTakenCounter >= excellent or mitigatedCounter >= excellent:
        snowballing +=1.5
    else:
        if dmgDealtCounter <= poor and dmgTakenCounter <= poor and mitigatedCounter <= poor:
            work_on_snowball.append("ROLE2")
        else:
            work_on_snowball.append("ROLE")
    # a snowballing player takes small leads and accelerates them into larger ones, by punishing mistakes from the enemy
    # a snowballer would typically focus on farming to scale up, or get kills to increase damage and ability to carry
    # a snowballer may give up objectives, but typically will ensure that they make up for that with something (an objective on the other side of the map, turret pressure, more kills)
    # a snowballer does not always play for the late game, they may want to use their obtained advantages to close out a game quickly (they do not want to give too many objectives like dragons, they don't want to lose barons, as well as do not want to give shutdowns)
    # a snowballer will take their leads to the rest of the map, and make sure their teammates also get a lead




    if kdaCounter >= excellent:
        fighting +=1.5
    else:
        if kdaCounter < poor:
            work_on_teamfight.append("KP2")
        else: 
            work_on_teamfight.append("KP")
    if deathCounter >= excellent:
        fighting +=1.5
    else:
        work_on_teamfight.append("DEATHS")
    if dmgDealtCounter >= excellent or dmgTakenCounter >= excellent or (ccCounter >= excellent and mitigatedCounter >= excellent) or healCounter >= excellent:
        fighting +=1
    else:
        work_on_teamfight.append("ROLE")
    if towerCounter >= excellent:
        fighting +=0.5
    else:
        work_on_teamfight.append("TOWER")
    if vsnCounter >= excellent:
        fighting +=0.5
    else:
        work_on_teamfight.append("VISION")
    if goldCounter >= excellent:
        fighting +=0.5
    else:
        work_on_teamfight.append("GOLD")
    if xpCounter >= excellent:
        fighting +=1
    else:
        work_on_teamfight.append("XP")
    if dragCounter >= excellent or baronCounter >= excellent:
        fighting += 1.5
    else:
        if baronCounter <= poor and dragCounter <= poor:
            work_on_teamfight.append("OBJECTIVE2")
        else:
            work_on_teamfight.append("OBJECTIVE")

    # a teamfighter will try to have the greatest impact on the game state by creating havoc for the enemy team through grouped fights
    # they will typically do/take a lot of damage, maybe mitigate a lot of dmg, maybe have good cc
    # the longer they last in the fights, the better chance their team has of winning
    # if they die quickly or get caught out, they may give up an opportunity or lose advantages




    if str(player.stats.lane) != "Lane.jungle":
        if deathCounter >= excellent:
            splitting +=0.5
        else:
            work_on_splitpush.append("DEATHS")
        if xpCounter >=excellent:
            splitting +=1 
        else:
            if xpCounter <=poor:
                work_on_splitpush.append("XP2")
            else:
                work_on_splitpush.append("XP")
        if towerCounter >= excellent:
            splitting +=1
        else:
            work_on_splitpush.append("TOWER")
        if turretDmg >= excellent:
            splitting +=2
        else:
            work_on_splitpush.append("DMG")
        if midLead >= excellent:
            splitting +=1.5
        else:
            work_on_splitpush.append("MID")
        if lateLead < excellent:
            work_on_splitpush.append("LATE")
        if  inhibCounter >= good:
            splitting +=1 
        else:
            work_on_splitpush.append("INHIB")
        if firstTowerCounter >= excellent:
            splitting +=0.5
        else:
            work_on_splitpush.append("FT")
        if baronCounter < excellent:
            work_on_splitpush.append("BARON")
        if riftCounter >= excellent:
            splitting +=0.5
        else:
            work_on_splitpush.append("HERALD")
    else:
        if deathCounter >= excellent:
            splitting +=0.5
        else:
            work_on_splitpush.append("DEATHS")
        if xpCounter >=excellent:
            splitting +=1 
        else:
            if xpCounter <=poor:
                work_on_splitpush.append("XP2")
            else:
                work_on_splitpush.append("XP")
        if towerCounter >= excellent:
            splitting +=0.5
        else:
            work_on_splitpush.append("TOWER")
        if turretDmg >= excellent:
            splitting +=1.5
        else:
            work_on_splitpush.append("DMG")
        if midLead >= excellent:
            splitting +=1
        else:
            work_on_splitpush.append("MID")
        if lateLead < excellent:
            work_on_splitpush.append("LATE")
        if inhibCounter >= good:
            splitting +=1 
        else:
            work_on_splitpush.append("INHIB")
        if firstTowerCounter >= excellent:
            splitting +=1
        else:
            work_on_splitpush.append("FT")
        if baronCounter < excellent:
            work_on_splitpush.append("BARON")
        if riftCounter >= excellent:
            splitting +=1.5
        else:
            work_on_splitpush.append("HERALD")
        # a splitpusher will try their best to create pressure on one part of the map while their team and the enemy are fighting on an objective
        # a good splitpusher will be able to attract multiple members towards a lane where they are pushing by having dueling threat, higher level, and/or higher gold
        # they can make the mistake of getting caught out, whether the enemy is giving an objective or simply not paying attention to the enemies' location
        # a good splitpusher will be able to open up a lane, possibly destroying an inhibitor as well
        # because of these destroyed inhibitors, they will be able to contest later objectives like barons and/or elders because of pushing super minions
    context["splitting"] = splitting
    context["s"] = (splitting/8) * 100
    context["fighting"] = fighting
    context["f"] = (fighting/8)*100
    context["aggression"] = aggression
    context["a"] = (aggression/8)*100
    context["snowballing"] = snowballing
    context["sn"] = (snowballing/8)*100

    playstyle = [splitting, aggression, fighting, snowballing]

    context["feedback"] = []
    context["style"] = []
    if max(playstyle) < 1:
        context["style"].append("You do not have a defined playstyle - understand your champion's identity in order to get effective feedback")
        return render(request, 'analysis/analysis.html', context)
    if max(playstyle) == splitting:
        context["style"].append("Your playstyle is splitting")
        if "DEATHS" in work_on_splitpush:
            context["feedback"].append(["Dying","You need to work on dying less frequently, typically splitpushers die when they are either collapsed/ganked in sidelane, or they partake in a teamfight which isn't in their favour"])
        if "XP" in work_on_splitpush:
            context["feedback"].append(["Experience","You need to work on getting more experience than your opponent, if you are unable to do so, you aren't creating enough pressure in your sidelane."])
        if "XP2" in work_on_splitpush:
            context["feedback"].append(["Experience (Important)","You need to work on getting more experience than your opponent, if you are unable to do so, you aren't creating enough pressure in your sidelane."])
        if "TOWER" in work_on_splitpush:
            context["feedback"].append(["Towers","You need to work on getting more turrets in order to open up the map for your teammates, along with getting a gold lead"])
        if "DMG" in work_on_splitpush:
            context["feedback"].append(["Damage","You need to do more damage to turrets, if you are not putting up enough damage to the turrets, you aren't contributing much to your team while splitpushing"])
        if "MID" in work_on_splitpush:
            context["feedback"].append(["Mid-Game","You need to find ways to obtain a mid-game lead over your opponent. Understanding your champion and how to win lane matchups is the best way to do so."])
        if "LATE" in work_on_splitpush:
            context["feedback"].append(["Late-Game","You create most pressure while splitpushing in the late game. If you are able to get a lead over your opponent in the late game, you will typically be able to attract more members towards the lane you are pushing, giving your team a numbers advantage on objectives like dragons and barons"])
        if "INHIB" in work_on_splitpush:
            context["feedback"].append(["Inhibitors","One of the most effective ways to create pressure without even going into a lane is having a pushing wave. Super minions are good at doing so, because they will require at least one person to defend, or they will 'splitpush' by themselves. Getting the first inhibitor can be really useful for you team, because you can end up in a win-win situation, where you either get turrets or drags/barons"])
        if "FT" in work_on_splitpush:
            context["feedback"].append(["First Tower","Although it may not happen every game due to the nature of LoL, getting the first turret is a great way to begin a splitpush (gives gold, allows for a laneswap with any losing lane, allows for further pressure in your lane, etc.)"])
        if "BARON" in work_on_splitpush:
            context["feedback"].append(["Barons","You want your team getting the baron nashor, because it makes your splitpush even stronger, and also allows for your team to seige. Whether you obtain it through pressure or by contributing to the teamfight, you want to make sure you get it whenever you can."])
        if "HERALD" in work_on_splitpush:
            context["feedback"].append(["Heralds","If your jungler is topside and you have a pushing lane top/mid and an even lane top/mid, you can try and take the rift-herald. Typically they will use it in the lane which is splitpushing/gives more plates. This allows for even more gold and opens up a lane more. Always try and get your jungler to take the herald when it is free."])
    if max(playstyle) == aggression:
        context["style"].append("Your playstyle is aggression")
        if "KP" in work_on_aggression:
            context["feedback"].append(["Kill Participation","You always want to make sure that you are making your enemies have minimal impact on the map, and therefore, should ideally have more kill participation. One of the best ways to do so is by roaming when you push in your lane, or counter jungling when the enemy jungler shows on the other side of the map/you know you are stronger"])
        if "DEATHS" in work_on_aggression:
            context["feedback"].append(["Dying","Playing aggressive and playing carelessly are two different things. Although it is important to try out different things and maybe even limit test a little bit, you need to make sure that you are not carelessly dying and giving away leads"])
        if "VISION" in work_on_aggression:
            context["feedback"].append(["Vision","When playing aggressively, you want to get vision on the enemy. You always want to have as much information as possible before you play aggressive. Typically you want to place wards on either the enemy jungler's camps, or deny your opponent vision, so that you can gank/trade/roam more"])
        if "FARM" in work_on_aggression:
            context["feedback"].append(["Farming","You want to make sure that you have more farm than your enemy when you are playing aggressive, because you want to be denying them any lead they try to get"])
        if "XP" in work_on_aggression:
            context["feedback"].append(["Experience","Having more experience than your opponent is very necessary in order to have maximum control over the game. If your opponent has an level powerspike in their kit which you do not get, you are technically behind, unless you have a very significant gold lead"])
        if "DRAG" in work_on_aggression:
            context["feedback"].append(["Dragons","Getting dragons is very important when playing aggressive, because you are typically playing an early game champion. If you give the enemy dragons, you extend the length of the game and allow them to scale. Even if they do not necessarily scale, giving the dragon soul is a huge buff for the opponent. Always try to secure dragons in order to close out a game"])
        if "BARON" in work_on_aggression:
            context["feedback"].append(["Barons","The baron is typically the game-finisher if you are playing properly when you are playing aggressive. If you get an early baron, you will be able to push very easily, get a lot of gold, and maybe even end the game if you have/can create the opportunity"])
        if "EARLY" in work_on_aggression:
            context["feedback"].append(["Early-Game","Early game aggression is the most important. You have the most control over a game at the earliest parts, the later a game goes, the less control you have. If you are able to deny your opponent and have impact on other lanes as early as possible, you will have the highest chance of winning the game."])
        if "EARLY2" in work_on_aggression:
            context["feedback"].append(["Early-Game (Important)","Early game aggression is the most important. You have the most control over a game at the earliest parts, the later a game goes, the less control you have. If you are able to deny your opponent and have impact on other lanes as early as possible, you will have the highest chance of winning the game."])
        if "MID" in work_on_aggression:
            context["feedback"].append(["Mid-Game","The mid game is where most aggressive players can easily give leads to their opponent. Many players deny their opponent early, but then forget/ignore them and allow them to scale up and come back into the game"])
        if "FB" in work_on_aggression:
            context["feedback"].append(["First Blood","Not a very important characteristic of aggressive players, but if you play an early game champion, you may want to try and invade with your team in order to get a quick and easy advantage"])

    if max(playstyle) == fighting:
        context["style"].append("Your playstyle is fighting")
        if "KP" in work_on_teamfight:
            context["feedback"].append(["Kill Participation","Having more kill participation than your opponent means that you are typically partaking in plays more often than them. If this is consistently the case, you will typically end up getting more objectives and towers."])
        if "KP2" in work_on_teamfight:
            context["feedback"].append(["Kill Participation (Important)","Having more kill participation than your opponent means that you are typically partaking in plays more often than them. If this is consistently the case, you will typically end up getting more objectives and towers."])
        if "DEATHS" in work_on_teamfight:
            context["feedback"].append(["Dying","Dying is a very common thing when playing solo queue. As a fighter, you should understand why you are dying. Are you getting caught out while making a pick, or chasing, or partaking in a fight which you should not take part in? There are lots of reasons why you could be giving unnecessary gold which can convert into objectives to the opponent."])
        if "ROLE" in work_on_teamfight:
            context["feedback"].append(["Team Role","Playing your role in fights is also very important. You should know whether you should be dishing out a lot of damage, or taking a lot of damage, or CCing the opponents, or healing your team, based on your role in the game. You should also know how to play for a teamfight, and how to position (ex. an assassin would look for a flank, cc/frontline would look to peel, marksman/mage would stay away from enemy threat and deal damage)"])
        if "TOWER" in work_on_teamfight:
            context["feedback"].append(["Towers","Seiging is the best way to win a game. Without any towers, you will limit your vision control, pressure in lanes, and ability to get objectives. Although you may play for teamfights and other objectives, you have to know when you should push for towers, otherwise, you are just wasting a lot of time, gold, and opportunities."])
        if "VISION" in work_on_teamfight:
            context["feedback"].append(["Vision","Having good vision in teamfights is the best way to have more information for your team, as well as making it so your team cannot die to a flank/surprise. The best way to get vision on an objective is to arrive early before it spawns and set your own vision, and deny enemy vision."])
        if "GOLD" in work_on_teamfight:
            context["feedback"].append(["Gold","Having more gold than your opponent in a teamfight typically means that it will be easier for you to play your role effectively. Although individual gold is not the most important thing for teamfighting, it can be helpful."])
        if "XP" in work_on_teamfight:
            context["feedback"].append(["Experience","Having more experience than your opponent means that you will have higher upgraded abilities and base stats. This will make you a bigger threat to the opponent."])
        if "OBJECTIVE" in work_on_teamfight:
            context["feedback"].append(["Objectives","Objectives are usually where you will be teamfighting. To either contest an objective, or to force it. If you are not getting objectives very often, you are not teamfighting correctly."])
        if "OBJECTIVE2" in work_on_teamfight:
            context["feedback"].append(["Objectives (Important)","Objectives are usually where you will be teamfighting. To either contest an objective, or to force it. If you are not getting objectives very often, you are not teamfighting correctly."])

    if max(playstyle) == snowballing:
        context["style"].append("Your playstyle is snowballing")
        if "FARM" in work_on_snowball:
            context["feedback"].append(["Farming","Farming is usually the best way to get a snowball going. Even if you are playing a champion that does not necessarily snowball though farming, it is a good way to keep the snowballing threat going, as you will always be in a position to get kills."])
        if "FARM2" in work_on_snowball:
            context["feedback"].append(["Farming (Important)","Farming is usually the best way to get a snowball going. Even if you are playing a champion that does not necessarily snowball though farming, it is a good way to keep the snowballing threat going, as you will always be in a position to get kills."])
        if "KP" in work_on_snowball:
            context["feedback"].append(["Kill Participation","Kill participation defines a snowballer, as it shows how well they are able to take an opportunity and create/extend a lead. Getting more kill participation is necessary to have an impact on the game."])
        if "DEATHS" in work_on_snowball:
            context["feedback"].append(["Dying","Dying is the easiest way to lose a snowballing lead, if you are giving away large shutdowns or getting caught before objectives or just dying for no significant reason, you are losing your ability to carry the game."])
        if "OBJECTIVE" in work_on_snowball:
            context["feedback"].append(["Objectives","Typically as a snowballer, you will be the biggest threat for the opponent. Therefore, you should be able to play threateningly enough to get the objectives. The difficult part about doing so is finding the balance between playing too aggressive and dying, and playing too passive (KDA player)."])
        if "BARON" in work_on_snowball:
            context["feedback"].append(["Barons","Getting barons is the key to closing out games as a snowballer. You will usually win your games if you get the baron and pressure lanes."])
        if "MID" in work_on_snowball:
            context["feedback"].append(["Mid-Game","The mid game is where you should be strongest as a snowballer. It is the point of the game where you can make the greatest impact and get advantages for your team. You want to make sure you have an advantage over your opponent during this time."])
        if "TOWER" in work_on_snowball:
            context["feedback"].append(["Towers","Getting towers is an important factor to win games in general. If you have more towers, you will get more vision areas, jungle camps, and therefore have better chances to get objectives."])
        if "VISION" in work_on_snowball:
            context["feedback"].append(["Vision","Vision can give your team more information, as well as deny the enemy information. Having good vision control is the best way to make more guaranteed plays."])
        if "ROLE" in work_on_snowball:
            context["feedback"].append(["Team Role","Playing your role in teamfights is very important when snowballing. You should typically be able to attract the attention of multiple members on the enemy team if you are playing your role correctly. This will make it a lot easier for your team to win fights and convert leads."])
        if "ROLE2" in work_on_snowball:
            context["feedback"].append(["Team Role (Important)","Playing your role in teamfights is very important when snowballing. You should typically be able to attract the attention of multiple members on the enemy team if you are playing your role correctly. This will make it a lot easier for your team to win fights and convert leads."])
    if len(context["feedback"]) == 0:
        context["feedback"].append("Good job!", "We have not detected anything that you should work on in your current playstyle, keep playing as you are and you should climb!")

    return render(request, 'analysis/analysis.html', context)


def about(request):
    context = {
        'posts':Playstyle.objects.all()
    }
    return render(request, 'analysis/about.html', context)

def search(request):
    return render(request, 'analysis/search.html')
# make the search site (after you register) which will have a form and be the one where you search for your champion using your summoner name
# 