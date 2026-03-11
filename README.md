# NoPing for Slack
[![built at | Hack Club](https://img.shields.io/badge/built_at-Hack_Club-%23ec3750?logo=hackclub)](https://hackclub.com)

<b>NoPing</b> is a Slack app that adds the `/np` command, letting you link to a user without mentioning (pinging) them.

Say you're helping someone in a help channel. You need to tell someone to DM a user, but you don't want to annoy them with a ping.

You could write:
> cc @/twonum

But that's just a short-term solution. What if "twonum" changes their display name to something else? The user also has to find that "twonum," so they can't just click a link to their profile.

That's what NoPing solves. Instead of using someone's (possibly volatile) display name, NoPing replaces regular Slack mentions with look-alike links (like [@twonum]), referencing their unique, permanent user ID. NoPing links still open the user's profile, but will not mention them. So, you would get this:
> cc [@twonum]

## How do I use it?
`/np Your message here! Now @twonum won't get annoyed.` That's the basic syntax; it replaces @twonum with [@twonum], the ping-free profile link.

### Advanced usage
#### "Escape" a mention
Want to mention someone anyway in a NoPing message? Escape the ping by putting a backslash (`\`) right after it. Keep in mind: The backslash needs to be either immediately after the ping or be separated by only a single space.
> `/np @twosta \, you can DM @twonum for help.` – This will replace [@twonum]'s mention, but not @twosta's.

#### Reply in a thread with NoPing
Slack bot commands like `/np` don't work in threads. Instead, use the "Reply in thread" message shortcut ("Connect to apps" option in message menus) on any message associated with the thread (either the parent message or any replies). This will open a modal dialog that lets you compose a message, which will be sent as a reply to the thread.

#### Use `/npp` to preview a message
The `/npp` (NoPing preview) command works just like `/np`, but instead of sending messages directly, it sends an ephemeral ("only visible to you") message (or opens a modal if you use it in a private channel NoPing is not in or if you use `/npp -m`).

`/npp` is helpful if you want to check what NoPing sends, if you want to be able to delete your messages, or if you want to use NoPing in a private channel without inviting it.

#### Edit a NoPing message
Use the "Edit NoPing message" shortcut like how you would reply in a thread. This opens a modal dialog where you can edit your message. I might get the modal to autofill your old message.

#### Message deletion
As NoPing "impersonates" your display name and profile icon, it cannot delete its messages without using a highly privileged admin token, which someone like [@twonum] would probably not get. The `/npp` command lets you see how the message would appear without sending it as NoPing, letting you copy and paste it, but it takes longer than just using `/np`.

## FAQ
### Why does NoPing mention me at the top of each message (like "<b>[@twonum]</b>:") if it already shows my name?
This is to prevent someone from simply changing their display name and profile icon to that of, for example, an official Hack Club staff member, then simply rename themselves back to hide it. NoPing will always add an ID-based mention back to the user who used a NoPing command.

This also lets NoPing work without a database. By not using a database, NoPing can stay lightweight by simply checking the first line of the message for a mention to the user's ID.

Slack limitations prevent impersonation from simply referencing a user ID; it only allows a username and profile icon to be shown.

#### What about other bots (at-channel)? They don't mention the user.
Bots like at-channel only allow the channel's manager to use its commands; however, NoPing can be used by anyone in any channel. at-channel users can be verified by checking a channel's managers, but for NoPing, its own user identity verification is required.

#### Why not just use OAuth and send messages directly as me?
Because an OAuth token would allow [@twonum] to send anything to any channel. They do not wish to possess such a token.

### NoPing is not working in my private channel!
Due to Slack limitations, you need to invite NoPing first by using `/invite @NoPing` in the channel.

#### But that means [@twonum] can see my messages!
You're absolutely right to be concerned about this. I take security with NoPing seriously.

NoPing data and any messages it has access to (other than its bot/app tokens and signing secret) are never stored on disk. It does not have a database and everything it processes is only in memory. The bot and app tokens are guarded and are revoked if they (in the very unlikely scenario) do leak.

NoPing does not read any existing messages except if someone uses the "Edit NoPing message" shortcut, in which case, it will read the message only to check ownership and then deletes it from memory.

If you're concerned about privacy, you can either use /npp preview for less access or use the NoPing source code and host your own NoPing-based bot, but don't use "np" or "NoPing" in the commands or message shortcuts to avoid confusion. (Feel free to use "NoPing" in the bot description, but not the bot's name.)

### How does NoPing hide the link preview?
NoPing links add a query string (`?noping=1`), which suppresses the link preview. This is a hacky workaround and probably is not stable.

### How does NoPing use my username and profile icon? ("Impersonation")
NoPing uses Slack API's "impersonation" feature to show your own details, making conversations a bit more straightforward. NoPing never does this without you explicitly using `/np` or "Reply in thread," and only does so for a single message.

#### I changed my Slack display name and profile icon, but NoPing messages still show the old one.
Unfortunately, this is due to Slack limitations not allowing impersonation to simply reference a user ID and instead has to be done manually, essentially hardcoding it into the message. Using `/npp` message preview is the only secure way to send messages directly as your own account.

## License
NoPing is licensed under GPLv3. See [COPYING](./COPYING).

[@twonum]: https://hackclub.slack.com/team/U094NTBR1S5?noping=1 "@twonum"
