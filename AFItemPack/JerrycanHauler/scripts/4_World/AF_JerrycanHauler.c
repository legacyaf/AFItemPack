// The pack's "Shoulder" slot is the scabbard, so it takes firearms only.
// Without this, a shovel (which also fits "Shoulder") dropped on the pack lands in the
// scabbard before its own slot, and a rifle can then no longer be attached.
class AF_JerrycanHauler extends Clothing
{
	override bool CanReceiveAttachment(EntityAI attachment, int slotId)
	{
		if (slotId == InventorySlots.GetSlotIdFromString("Shoulder") && !attachment.IsWeapon())
			return false;

		return super.CanReceiveAttachment(attachment, slotId);
	}
};
