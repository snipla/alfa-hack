<?php

namespace App\Filament\Resources\Requests\Pages;

use App\Filament\Resources\Requests\RequestResource;
use App\Models\Request;
use Filament\Actions\Action;
use Filament\Actions\DeleteAction;
use Filament\Actions\ViewAction;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Infolists\Components\TextEntry;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\EditRecord;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Schema;
use Filament\Support\Icons\Heroicon;

class ManageRequests extends EditRecord
{
    protected static string $resource = RequestResource::class;

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextEntry::make('id')
                    ->columnSpan(1)
                    ->columnStart(1)
                    ->label('ID заявки'),
                Section::make([
                    Textarea::make('admin_comment')
                        ->columnSpanFull()
                        ->required()
                        ->autosize()
                        ->placeholder('Дайте комментарий по заявке'),
                    Action::make('accept')
                        ->label('Принять заявку')
                        ->color('success')
                        ->requiresConfirmation()
                        ->modalIcon('heroicon-o-exclamation-circle')
                        ->modalHeading('Одобрить заявку') // Заголовок
                        ->modalDescription('Вы уверены, что хотите одобрить эту заявку?')
                        ->modalSubmitActionLabel('Да, одобрить') // Текст кнопки подтверждения
                        ->action(function ($record, array $data, $get) {
                            $record->admin_comment = $get('admin_comment');
                            $record->status = Request::REQUEST_ACCEPTED;
                            $record->save();
                            redirect(RequestResource::getUrl());
                        }),
                    Action::make('reject')
                        ->label('Отклонить заявку')
                        ->color('danger')
                        ->requiresConfirmation()
                        ->modalIcon('heroicon-o-exclamation-circle')
                        ->modalHeading('Отклонить заявку') // Заголовок
                        ->modalDescription('Вы уверены, что хотите отклонить эту заявку?')
                        ->modalSubmitActionLabel('Да, отклонить') // Текст кнопки подтверждения
                        ->modalIconColor('danger')
                        ->action(function ($record, array $data, $get) {
                            $record->admin_comment = $get('admin_comment');
                            $record->status = Request::REQUEST_REJECTED;
                            $record->save();
                            redirect(RequestResource::getUrl());
                        }),
                ])
                    ->columns(1)
                    ->columnSpan(2)
                    ->columnStart(2),

            ])
            ->columns(3)
            ->statePath('data') // Все данные формы будут храниться в свойстве $data
            ->record($this->getRecord()); // Привязка формы к текущей записи
    }

    protected function getFormActions(): array
    {
        return array_merge([

//            $this->getSaveFormAction()
//                ->label('Применить'),
//            $this->getCancelFormAction()
//                ->label('Назад')
//                ->url($this->getResource()::getUrl('index')),
        ]);
    }

    protected function getHeaderActions(): array
    {

        return [
            ViewAction::make(),
            DeleteAction::make(),
        ];
    }
}
