_feed_em_completion() {
    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
                   COMP_CWORD=$COMP_CWORD \
                   _FEED_EM_COMPLETE=complete $1 ) )
    return 0
}

complete -F _feed_em_completion -o default feed-em;
