/*
 * Copyright (C) 2024 Michael Piazza
 *
 * This file is part of Smart Notes.
 *
 * Smart Notes is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Smart Notes is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Smart Notes. If not, see <https://www.gnu.org/licenses/>.
 */

import { useState } from "react"

import { errorMessage } from "@/lib/errors"
import { sendFeedback } from "@/services/commands"

interface FeedbackFormState {
  error: string | null
  isSending: boolean
  message: string
  sent: boolean
}

interface SetMessageOptions {
  resetSent?: boolean
}

interface UseFeedbackFormOptions {
  clearMessageOnSuccess?: boolean
}

const INITIAL_STATE: FeedbackFormState = {
  error: null,
  isSending: false,
  message: "",
  sent: false,
}

export const useFeedbackForm = ({
  clearMessageOnSuccess = false,
}: UseFeedbackFormOptions = {}) => {
  const [state, setState] = useState<FeedbackFormState>(INITIAL_STATE)
  const patch = (partial: Partial<FeedbackFormState>) =>
    setState((current) => ({ ...current, ...partial }))
  const setMessage = (
    message: string,
    { resetSent = false }: SetMessageOptions = {},
  ) => patch({ message, ...(resetSent ? { sent: false } : {}) })

  const submit = async () => {
    patch({ error: null, isSending: true, sent: false })
    try {
      await sendFeedback({ message: state.message.trim() })
      patch({
        ...(clearMessageOnSuccess ? { message: "" } : {}),
        isSending: false,
        sent: true,
      })
    } catch (error) {
      patch({
        error: errorMessage(error, "Could not send feedback"),
        isSending: false,
      })
    }
  }

  return {
    isSubmitDisabled: state.isSending || state.message.trim() === "",
    patch,
    setMessage,
    state,
    submit,
  }
}
