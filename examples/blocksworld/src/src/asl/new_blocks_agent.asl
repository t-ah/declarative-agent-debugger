// plans for general stuff

!tests.
+!tests <-
    !test2;
    !test3;
    !noApplicablePlanButRecovery(3);
    !!failLater;
    !!testNoApplicablePlan;
    !recover;
    wait.

+!noApplicablePlanButRecovery(4) <-
    .print("This plan is not applicable.").

-!noApplicablePlanButRecovery(_) <-
    .print("Recovering after no applicable plan.").

+!test2 <-
    .fail;
    .print("Unreachable instruction").

-!test2 <-
    wait.

+!test3 <-
    .print("test 3");
    !mySubPlanWillFailButIRecover;
    .print("test 3 recovered").

+!mySubPlanWillFailButIRecover <-
    !failNow.

-!mySubPlanWillFailButIRecover <-
    .print("recovered for test 3 after sub-plan failed").

+!failLater <-
    wait;
    !failNow.

+!failNow <-
    .fail.

+!recover <-
    .fail;
    .print("Unreachable instruction").

-!recover <-
    !recoverNow.

+!recoverNow <-
    wait.

+!testNoApplicablePlan <-
    !failBecauseThereIsNoPlanForThis.


// plans for the blocksworld

+task(Id,_) : busy.

+task(Id, Colour) : not busy <-
    +busy;
    !completeTask(Id, Colour).

+task(Id, Colour) : busy <-
    +openTask(Id, Colour).

+!completeTask(Id, Colour) <-
    !prepared;
    !holding(Colour);
    !processed;
    !delivered;
    !deliveryChecked(Id).

+!prepared : task(Colour) & holding(Block) & not colour(Block, Colour) <-
    putDown;
    !prepared.

+!prepared <-
    !charged;
    !reset.

+!reset <-
    .abolish(visited(_)).

+!charged : energy(MyEnergy) & MyEnergy < 80 <-
    recharge;
    !charged.

+!charged <-
    wait.

+!holding(Colour) : holding(Block) & colour(Block, Colour) <-
    wait.

+!holding(Colour) : colour(Block,Colour) <-
    gotoBlock(Block);
    pickUp.

+!holding(Colour) : not colour(_, Colour) <-
    !found(Colour);
    ?colour(Block, Colour);
    gotoBlock(Block);
    pickUp.

+!found(Colour) : not colour(_, Colour) & place(Place) & not visited(Place) <-
    goto(Place);
    +visited(Place);
    !found(Colour).

+!found(Colour) : colour(_, Colour) <-
    wait.

+!processed : not packaging <-
    wait.

+!processed : packaging <-
    goto(packing);
    putDown;
    activate.

+!delivered <-
    goto(dropzone);
    putDown.

+!deliveryChecked(Id) : delivered(Id) <-
    ?delivered(Id);
    -busy.

+!deliveryChecked(_) <-
    .print("I am Error.").