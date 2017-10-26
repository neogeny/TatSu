" Vim syntax file
" Language:         EBNF/Tatsu
" Maintainer:       Apalala
" With thanks to Michael Brailsford for the BNF syntax file.

" Quit when a syntax file was already loaded
if version < 600
  syntax clear
elseif exists("b:current_syntax")
  finish
endif

syn match ebnfInclude /#[ \t\n]*[A-Za-z0-9_-]\+/  skipwhite skipempty nextgroup=ebnfParamStart
syn match ebnfRuleInclude />[ \t\n]*[A-Za-z0-9_-]\+/  skipwhite skipempty
syn match ebnfMetaIdentifier /[A-Za-z0-9_-]\+/ skipwhite skipempty nextgroup=ebnfSeparator
syn match ebnfName /@:\|@+:\|@\|[A-Za-z0-9_-]\+:\|[A-Za-z0-9_-]\++:/ contained skipwhite skipempty
syn match ebnfDecorator /@@\?[A-Za-z0-9_-]\+/ skipwhite skipempty


syn match ebnfInherit /<[ \t\n]*[A-Za-z0-9_-]\+/  skipwhite skipempty nextgroup=ebnfParamStart,ebnfSeparator

syn match ebnfParamsStart "::" nextgroup=ebnfParams skipwhite skipempty
syn match ebnfParams /.*[^=]/ contained skipwhite skipempty nextgroup=ebnfSeparator
syn region ebnfParams start=/(/ end=')' skipwhite skipempty nextgroup=ebnfSeparator


syn match ebnfSeparator /[=]/ contained nextgroup=ebnfProduction skipwhite skipempty
syn region ebnfProduction start=/\zs[^;]/ end=/[;]/me=e-1 contained contains=ebnfSpecial,ebnfDelimiter,ebnfTerminal,ebnfConstant,ebnfSpecialSequence,ebnfPattern,ebnfComment,ebnfName,ebnfRuleInclude nextgroup=ebnfEndProduction skipwhite skipempty
syn match ebnfDelimiter #[\-\*+]\|>>\|[&~,(|)\]}\[{!]\|\(\*)\)\|\((\*\)\|\(:)\)\|\((:\)# contained
syn match ebnfSpecial /[~+*%\.]/ contained
syn region ebnfPattern matchgroup=Delimiter start=/\// end=/\// contained
syn region ebnfSpecialSequence matchgroup=Delimiter start=/?\// end=/\/?/ contained
syn match ebnfEndProduction /[;]/ contained
syn region ebnfTerminal matchgroup=delimiter start=/"/ end=/"/ contained
syn region ebnfTerminal matchgroup=delimiter start=/'/ end=/'/ contained
syn region ebnfConstant matchgroup=delimiter start=/`/ end=/`/ contained

syn region ebnfComment start="#" end="$" contains=ebnfTodo
syn region ebnfComment start="(\*" end="\*)" contains=ebnfTodo
syn keyword ebnfTodo        FIXME NOTE NOTES TODO XXX contained

syn region ebnfClosure start="'.{" end="}" contains=ebnfTodo


hi link ebnfComment Comment
hi link ebnfMetaIdentifier Identifier
hi link ebnfSeparator ebnfDelimiter
hi link ebnfEndProduction ebnfDelimiter
hi link ebnfDelimiter Delimiter
hi link ebnfDelimiter Delimiter
hi link ebnfSpecial Type
hi link ebnfSpecialSequence Statement
hi link ebnfPattern Statement
hi link ebnfTerminal String

hi link ebnfName Keyword
hi link ebnfRuleInclude Include
hi link ebnfDecorator Include
hi link ebnfConstant ebnfDecorator
hi link ebnfInherit Include
hi link ebnfParamsStart ebnfParams
hi link ebnfParams Type
hi link ebnfClosure Type
hi link ebnfTodo Todo
