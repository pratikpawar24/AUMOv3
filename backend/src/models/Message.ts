import mongoose, { Schema, Document } from "mongoose";

export interface IMessage extends Document {
  roomId: string;
  sender: mongoose.Types.ObjectId;
  content: string;
  type: "text" | "system" | "location";
  createdAt: Date;
}

const messageSchema = new Schema<IMessage>(
  {
    roomId: { type: String, required: true, index: true },
    sender: { type: Schema.Types.ObjectId, ref: "User", required: true },
    content: { type: String, required: true },
    type: { type: String, enum: ["text", "system", "location"], default: "text" },
  },
  { timestamps: true }
);

export const Message = mongoose.model<IMessage>("Message", messageSchema);
